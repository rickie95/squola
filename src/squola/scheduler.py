"""
Scheduling generation using Google OR-Tools CP-SAT solver.

This module fetches constraints from the database and generates
a valid weekly schedule for all classes, teachers, and matters.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from ortools.sat.python import cp_model
from sqlalchemy.orm import Session, joinedload

from squola.models import (
    ClassMatterAssignment,
    FixedClassLesson,
    MatterRequirements,
    SavedSchedule,
    SchedulePreference,
    SchoolClass,
    Teacher,
    TeacherUnavailability,
)

# Schedule constants
DAYS_OF_WEEK = 5  # Monday to Friday (0-4)
HOURS_PER_DAY = 6  # 8:00 to 14:00 (slots 1-6)
LEGAL_DAILY_TEACHING_HOURS = [0, 2, 3, 4, 5]
MAX_DAILY_ASSIGNMENT_HOURS = 3  # hours of one matter-class assignment in one day
LONG_RUN_WINDOW = 4  # consecutive teaching hours that start to hurt

# Objective weights. Only relative magnitudes matter: the solver compares
# alternatives, never absolute costs.
W_DAILY_BALANCE = 16
W_CLASS_BLOCK = 10
W_BREAK_DAY_STRICT = 8  # cost of the allowed break for a grouping preference
W_LONG_RUN = 6
W_BREAK_DAY = 1  # cost of the allowed break for everyone else
W_TIME_PREFERENCE = 1

# In a day that earns the allowance the break always removes at least one long
# run, because four hours without a gap in six slots have to be consecutive. So
# the break is worth W_LONG_RUN in a four-hour day and twice that in a five-hour
# one, and the two weights sit on either side of the smaller gain: the ordinary
# break stays worth buying in both, the grouping preference drops it in the
# four-hour day only. Checked here so that retuning W_LONG_RUN cannot silently
# collapse one of the two behaviours.
assert W_LONG_RUN > W_BREAK_DAY + 2 * W_TIME_PREFERENCE
assert (
    W_LONG_RUN
    < W_BREAK_DAY_STRICT + 2 * W_TIME_PREFERENCE
    < 2 * W_LONG_RUN
)

# Past the day's allowance a gap hour has to cost more than every other term can
# gain over a whole week, so that no other criterion can ever buy a second one.
# Derived from the other weights rather than tuned, because a hand-picked number
# drifts as soon as one of them changes. The weekly factor is not caution: moving
# a lesson to open a gap on one day also changes another, so a per-day bound
# would be an estimate instead of a proof.
W_EXCESS_GAP = 1 + DAYS_OF_WEEK * (
    HOURS_PER_DAY * W_CLASS_BLOCK
    + (HOURS_PER_DAY - LONG_RUN_WINDOW + 1) * W_LONG_RUN
    + HOURS_PER_DAY * W_DAILY_BALANCE
    + sum(W_TIME_PREFERENCE * (hour - 1) for hour in range(1, HOURS_PER_DAY + 1))
    + max(W_BREAK_DAY, W_BREAK_DAY_STRICT)
)
DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
HOUR_LABELS = [
    "08:00-09:00",
    "09:00-10:00",
    "10:00-11:00",
    "11:00-12:00",
    "12:00-13:00",
    "13:00-14:00",
]

# Daily cap requirements, mapped to the hours of one assignment they allow in a
# day. An assignment declaring several is capped by the tightest one, so the two
# never contradict each other.
DAILY_CAP_HOURS = {
    MatterRequirements.MAX_ONE_HOUR_PER_DAY: 1,
    MatterRequirements.MAX_TWO_HOURS_PER_DAY: 2,
}

# Requirements demanding a single lesson of a given length. A daily cap below
# that length makes them impossible to satisfy.
LESSON_LENGTH_HOURS = {
    MatterRequirements.ONE_LESSON_OF_TWO_HOURS_PER_WEEK: 2,
    MatterRequirements.ONE_LESSON_OF_THREE_HOURS_PER_WEEK: 3,
}


def resolve_daily_cap(requirements: list[MatterRequirements] | None) -> int:
    """Hours of one assignment allowed in a single day: the tightest cap declared."""
    caps = [DAILY_CAP_HOURS[req] for req in requirements or [] if req in DAILY_CAP_HOURS]
    return min(caps, default=MAX_DAILY_ASSIGNMENT_HOURS)


def requirement_conflict(
    requirements: list[MatterRequirements] | None,
    hours_per_week: int | None = None,
) -> str | None:
    """
    Why this combination of requirements can never be scheduled, or None.

    Only arithmetic that holds whatever the rest of the timetable looks like, so
    that a caller can refuse the write outright. Everything subtler - teacher
    unavailability, other classes competing for the same slots - stays the
    solver's to report as INFEASIBLE.

    hours_per_week is optional because a matter declares default requirements
    without knowing the weekly hours of the assignments that will carry them.
    """
    cap = resolve_daily_cap(requirements)
    longest_lesson = max(
        (
            LESSON_LENGTH_HOURS[req]
            for req in requirements or []
            if req in LESSON_LENGTH_HOURS
        ),
        default=0,
    )
    if cap < longest_lesson:
        return (
            f"a daily cap of {cap} hour(s) leaves no room for the required "
            f"lesson of {longest_lesson} hours"
        )
    if hours_per_week is not None and hours_per_week > cap * DAYS_OF_WEEK:
        return (
            f"{hours_per_week} weekly hours do not fit in {DAYS_OF_WEEK} days "
            f"capped at {cap} hour(s) each"
        )
    return None


def fully_unavailable_days(
    unavailabilities: list[TeacherUnavailability], teacher_id: int
) -> set[int]:
    """Return weekdays whose every teaching period is hard-blocked."""
    unavailable_by_day: dict[int, set[int]] = {}
    for slot in unavailabilities:
        if slot.teacher_id == teacher_id:
            unavailable_by_day.setdefault(slot.day_of_week, set()).add(slot.hour_slot)

    teaching_hours = set(range(1, HOURS_PER_DAY + 1))
    return {
        day for day, hours in unavailable_by_day.items() if hours == teaching_hours
    }


def teacher_workweek_infeasibility_message(
    data: "SchedulingData", teacher: Teacher
) -> str:
    """Explain the workweek rule that makes a teacher's isolated model infeasible."""
    weekly_hours = sum(
        assignment.hours_per_week
        for assignment in data.assignments
        if assignment.teacher_id == teacher.id
    )
    fully_blocked = fully_unavailable_days(data.unavailabilities, teacher.id)

    if teacher.prefers_day_off and not fully_blocked and weekly_hours > 4 * 5:
        return (
            f"Teacher {teacher.first_name} {teacher.last_name} has {weekly_hours} weekly "
            "hours, but a flexible day off requires at least one fully free weekday "
            "and permits at most 20 hours across the other four weekdays."
        )

    eligible_days = DAYS_OF_WEEK - len(fully_blocked)
    return (
        f"Teacher {teacher.first_name} {teacher.last_name} cannot distribute "
        f"{weekly_hours} weekly hours across all {eligible_days} eligible weekday(s) "
        "with 2 to 5 lessons per teaching day."
    )


@dataclass
class SchedulingData:
    """Data container for all scheduling-related information from the database."""

    # Core entities
    teachers: list[Teacher] = field(default_factory=list)
    classes: list[SchoolClass] = field(default_factory=list)
    assignments: list[ClassMatterAssignment] = field(default_factory=list)

    # Constraints data
    unavailabilities: list[TeacherUnavailability] = field(default_factory=list)
    fixed_lessons: list[FixedClassLesson] = field(default_factory=list)

    # Index mappings for OR-Tools (entity -> index)
    teacher_index: dict[int, int] = field(default_factory=dict)
    class_index: dict[int, int] = field(default_factory=dict)
    assignment_index: dict[int, int] = field(default_factory=dict)


@dataclass
class ScheduleSlot:
    """Represents a single scheduled slot in the timetable."""

    day: int  # 0-4 (Monday-Friday)
    hour: int  # 1-6 (hour slots)
    class_id: int
    class_name: str
    teacher_id: int
    teacher_name: str
    matter_id: int
    matter_name: str
    assignment_id: int


@dataclass
class GeneratedSchedule:
    """Container for the generated schedule and metadata."""

    slots: list[ScheduleSlot] = field(default_factory=list)
    status: str = "UNKNOWN"
    solve_time_seconds: float = 0.0
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    quality: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert schedule to dictionary for JSON serialization."""
        return {
            "metadata": {
                "status": self.status,
                "solve_time_seconds": self.solve_time_seconds,
                "generated_at": self.generated_at,
                "total_slots": len(self.slots),
                # Reported, never stored: save_schedule_to_db persists only the
                # "schedule" key, so saved timetables stay unchanged.
                **({"quality": self.quality} if self.quality is not None else {}),
            },
            "schedule": {
                "by_class": self._group_by_class(),
                "by_teacher": self._group_by_teacher(),
                "by_day": self._group_by_day(),
            },
        }

    def _group_by_class(self) -> dict[str, list[dict]]:
        """Group schedule slots by class."""
        result: dict[str, list[dict]] = {}
        for slot in self.slots:
            if slot.class_name not in result:
                result[slot.class_name] = []
            result[slot.class_name].append({
                "day": DAY_NAMES[slot.day],
                "hour": HOUR_LABELS[slot.hour - 1],
                "teacher": slot.teacher_name,
                "matter": slot.matter_name,
            })
        # Sort each class's slots by day and hour
        for class_name in result:
            result[class_name].sort(
                key=lambda x: (DAY_NAMES.index(x["day"]), HOUR_LABELS.index(x["hour"]))
            )
        return result

    def _group_by_teacher(self) -> dict[str, list[dict]]:
        """Group schedule slots by teacher."""
        result: dict[str, list[dict]] = {}
        for slot in self.slots:
            if slot.teacher_name not in result:
                result[slot.teacher_name] = []
            result[slot.teacher_name].append({
                "day": DAY_NAMES[slot.day],
                "hour": HOUR_LABELS[slot.hour - 1],
                "class": slot.class_name,
                "matter": slot.matter_name,
            })
        for teacher_name in result:
            result[teacher_name].sort(
                key=lambda x: (DAY_NAMES.index(x["day"]), HOUR_LABELS.index(x["hour"]))
            )
        return result

    def _group_by_day(self) -> dict[str, list[dict]]:
        """Group schedule slots by day."""
        result: dict[str, list[dict]] = {}
        for day_name in DAY_NAMES:
            result[day_name] = []
        for slot in self.slots:
            result[DAY_NAMES[slot.day]].append({
                "hour": HOUR_LABELS[slot.hour - 1],
                "class": slot.class_name,
                "teacher": slot.teacher_name,
                "matter": slot.matter_name,
            })
        for day_name in result:
            result[day_name].sort(key=lambda x: HOUR_LABELS.index(x["hour"]))
        return result

    def save_to_json(self, filepath: str | Path) -> None:
        """Save schedule to a JSON file."""
        filepath = Path(filepath)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)


def daily_band(total_hours: int, workdays: int) -> tuple[int, int]:
    """
    Balanced daily load band for a teacher: floor and ceil of their own weekly
    average.

    Derived rather than hardcoded, so it follows reduced hours and teachers who
    also work at another school without a special case. Clamped to the legal
    daily maximum, which already caps the load: a band above it is unreachable
    and clamping loses nothing.
    """
    if workdays <= 0:
        return (0, 0)
    return (
        min(total_hours // workdays, HOURS_PER_DAY),
        min(-(-total_hours // workdays), HOURS_PER_DAY),
    )


QUALITY_DIMENSIONS = (
    "class_blocks",
    "excess_gap_hours",
    "long_runs",
    "balance_deviation",
)
# Reported as totals but kept out of the worst list: a day served the way its
# teacher asked for is not an offender, and ranking it as one would bury the
# real defects.
QUALITY_INFO_DIMENSIONS = ("break_days", "missed_break_days")
QUALITY_WORST_ENTRIES = 5


def compute_quality_metrics(
    slots: list[ScheduleSlot],
    eligible_workdays: dict[int, int],
    unavailable: set[tuple[int, int, int]] | None = None,
) -> dict[str, Any]:
    """
    Score a timetable on the dimensions the day-shape objective optimises.

    Derived from the extracted slots alone, never from solver variables, so the
    same numbers can be computed for any timetable and asserted in tests without
    building a model. `eligible_workdays` maps a teacher to the weekdays they can
    teach on; it cannot be recovered from the slots, and using the days actually
    taught would score a concentrated week as perfectly balanced. `unavailable`
    holds the (teacher, day, hour) slots a teacher cannot teach in, for the same
    reason: without it these numbers would count gaps the solver never charged.
    """
    unavailable = unavailable or set()
    by_teacher_day: dict[tuple[int, int], dict[int, int]] = {}
    teacher_names: dict[int, str] = {}
    weekly_hours: dict[int, int] = {}

    for slot in slots:
        by_teacher_day.setdefault((slot.teacher_id, slot.day), {})[slot.hour] = slot.class_id
        teacher_names[slot.teacher_id] = slot.teacher_name
        weekly_hours[slot.teacher_id] = weekly_hours.get(slot.teacher_id, 0) + 1

    per_day: dict[tuple[int, int], dict[str, int]] = {}
    for key, class_by_hour in by_teacher_day.items():
        hours = sorted(class_by_hour)
        starts = sum(
            1 for hour in hours if class_by_hour.get(hour - 1) != class_by_hour[hour]
        )
        occupied = set(hours)
        teacher_id, day = key
        # Only free slots between two lessons count, and only those the teacher
        # could have taught in: before the first and after the last lesson they
        # are not at school, and in an unavailable slot they cannot be.
        gap_hours = sum(
            1
            for hour in range(hours[0], hours[-1] + 1)
            if hour not in occupied and (teacher_id, day, hour) not in unavailable
        )
        # A day long enough to be worth breaking is allowed one gap hour.
        allowance = 1 if len(occupied) >= LONG_RUN_WINDOW else 0
        per_day[key] = {
            # Starts beyond the number of distinct classes: the unavoidable
            # minimum for that day's classes is not a defect.
            "class_blocks": starts - len(set(class_by_hour.values())),
            "excess_gap_hours": max(0, gap_hours - allowance),
            "break_days": 1 if gap_hours else 0,
            "missed_break_days": 1 if allowance and not gap_hours else 0,
            "long_runs": sum(
                1
                for start in range(1, HOURS_PER_DAY - LONG_RUN_WINDOW + 2)
                if occupied.issuperset(range(start, start + LONG_RUN_WINDOW))
            ),
            "balance_deviation": 0,
        }

    for teacher_id, total in weekly_hours.items():
        low, high = daily_band(total, eligible_workdays.get(teacher_id) or DAYS_OF_WEEK)
        for day in range(DAYS_OF_WEEK):
            load = len(by_teacher_day.get((teacher_id, day), {}))
            if not load:
                continue  # a free weekday is not a day below the band
            per_day[(teacher_id, day)]["balance_deviation"] = max(
                0, load - high, low - load
            )

    totals = {
        dimension: sum(values[dimension] for values in per_day.values())
        for dimension in QUALITY_DIMENSIONS + QUALITY_INFO_DIMENSIONS
    }
    worst = {}
    for dimension in QUALITY_DIMENSIONS:
        offenders = [
            {
                "teacher": teacher_names[teacher_id],
                "day": DAY_NAMES[day],
                "value": values[dimension],
            }
            for (teacher_id, day), values in per_day.items()
            if values[dimension] > 0
        ]
        offenders.sort(key=lambda entry: (-entry["value"], entry["teacher"], entry["day"]))
        worst[dimension] = offenders[:QUALITY_WORST_ENTRIES]

    return {**totals, "worst": worst}


def fetch_scheduling_data(db: Session, workspace_id: int) -> SchedulingData:
    """
    Fetch all necessary data from the database for scheduling.

    This includes:
    - All teachers with their unavailabilities
    - All classes
    - All class-matter-teacher assignments
    """
    data = SchedulingData()

    # Fetch teachers with eager loading of unavailabilities
    data.teachers = list(
        db
        .query(Teacher)
        .filter(Teacher.workspace_id == workspace_id)
        .options(joinedload(Teacher.unavailabilities))
        .all()
    )

    # Fetch all classes
    data.classes = list(
        db.query(SchoolClass).filter(SchoolClass.workspace_id == workspace_id).all()
    )

    # Fetch all assignments with eager loading of related entities
    data.assignments = list(
        db
        .query(ClassMatterAssignment)
        .filter(ClassMatterAssignment.workspace_id == workspace_id)
        .options(
            joinedload(ClassMatterAssignment.teacher),
            joinedload(ClassMatterAssignment.school_class),
            joinedload(ClassMatterAssignment.matter),
        )
        .all()
    )

    # Fetch all unavailability slots
    data.unavailabilities = list(
        db
        .query(TeacherUnavailability)
        .filter(TeacherUnavailability.workspace_id == workspace_id)
        .all()
    )

    # Fetch fixed class lessons with their assignments
    data.fixed_lessons = list(
        db
        .query(FixedClassLesson)
        .filter(FixedClassLesson.workspace_id == workspace_id)
        .options(joinedload(FixedClassLesson.assignment))
        .all()
    )

    # Build index mappings
    for i, teacher in enumerate(data.teachers):
        data.teacher_index[teacher.id] = i

    for i, school_class in enumerate(data.classes):
        data.class_index[school_class.id] = i

    for i, assignment in enumerate(data.assignments):
        data.assignment_index[assignment.id] = i

    return data


class ScheduleGenerator:
    """
    OR-Tools CP-SAT based schedule generator.

    Creates decision variables and constraints based on the scheduling
    requirements and solves for a valid timetable.
    """

    def __init__(self, data: SchedulingData):
        self.data = data
        self.model = cp_model.CpModel()

        # Decision variables: x[assignment_id, day, hour] = 1 if assignment is scheduled
        # at that day and hour
        self.x: dict[tuple[int, int, int], cp_model.IntVar] = {}
        # (teacher_id, day) -> bool var, only for teachers with a flexible day off
        self.works_on_day: dict[tuple[int, int], cp_model.IntVar] = {}

        # Build reverse lookups for constraints
        self._build_lookups()

    def _build_lookups(self) -> None:
        """Build lookup dictionaries for efficient constraint creation."""
        # Assignments by teacher
        self.assignments_by_teacher: dict[int, list[ClassMatterAssignment]] = {}
        for assignment in self.data.assignments:
            if assignment.teacher_id not in self.assignments_by_teacher:
                self.assignments_by_teacher[assignment.teacher_id] = []
            self.assignments_by_teacher[assignment.teacher_id].append(assignment)

        # Assignments by class
        self.assignments_by_class: dict[int, list[ClassMatterAssignment]] = {}
        for assignment in self.data.assignments:
            if assignment.class_id not in self.assignments_by_class:
                self.assignments_by_class[assignment.class_id] = []
            self.assignments_by_class[assignment.class_id].append(assignment)

        # Unavailable slots by teacher: (teacher_id, day, hour) -> True
        self.unavailable: set[tuple[int, int, int]] = set()
        for slot in self.data.unavailabilities:
            self.unavailable.add((slot.teacher_id, slot.day_of_week, slot.hour_slot))
        self.fully_unavailable_by_teacher = {
            teacher.id: fully_unavailable_days(self.data.unavailabilities, teacher.id)
            for teacher in self.data.teachers
        }
        self.preference_by_teacher = {
            teacher.id: teacher.schedule_preference for teacher in self.data.teachers
        }

        # Assignments grouped by the class they are taught in, per teacher. Two
        # matters of the same teacher in the same class are one contiguous block:
        # the teacher does not move and the class does not change teacher.
        self.assignments_by_teacher_class: dict[int, dict[int, list[ClassMatterAssignment]]] = {}
        for assignment in self.data.assignments:
            by_class = self.assignments_by_teacher_class.setdefault(assignment.teacher_id, {})
            by_class.setdefault(assignment.class_id, []).append(assignment)

        # Weekdays a teacher can actually teach on, used to derive the balanced
        # daily band. A flexible day off only counts when no weekday is already
        # fully hard-blocked, matching the workload constraint.
        self.eligible_workdays: dict[int, int] = {}
        for teacher in self.data.teachers:
            blocked = len(self.fully_unavailable_by_teacher[teacher.id])
            flexible = 1 if teacher.prefers_day_off and not blocked else 0
            self.eligible_workdays[teacher.id] = DAYS_OF_WEEK - blocked - flexible

        # Build requirement-based assignment lookups
        self.at_least_twice_per_week_assignments: set[int] = set()
        self.lesson_of_three_hours_per_week_assignments: set[int] = set()
        self.lesson_of_two_hours_per_week_assignments: set[int] = set()

        for assignment in self.data.assignments:
            requirements = assignment.requirements or []
            for req in requirements:
                if req == MatterRequirements.AT_LEAST_TWICE_PER_WEEK:
                    self.at_least_twice_per_week_assignments.add(assignment.id)
                elif req == MatterRequirements.ONE_LESSON_OF_THREE_HOURS_PER_WEEK:
                    self.lesson_of_three_hours_per_week_assignments.add(assignment.id)
                elif req == MatterRequirements.ONE_LESSON_OF_TWO_HOURS_PER_WEEK:
                    self.lesson_of_two_hours_per_week_assignments.add(assignment.id)

        # Hours of a single assignment allowed in one day. Without a cap
        # requirement this is the system-wide MAX_DAILY_ASSIGNMENT_HOURS.
        self.daily_cap_by_assignment: dict[int, int] = {
            assignment.id: resolve_daily_cap(assignment.requirements)
            for assignment in self.data.assignments
        }

    def _create_variables(self) -> None:
        """Create decision variables for the CP model."""
        for assignment in self.data.assignments:
            for day in range(DAYS_OF_WEEK):
                for hour in range(1, HOURS_PER_DAY + 1):
                    var_name = f"x_a{assignment.id}_d{day}_h{hour}"
                    self.x[(assignment.id, day, hour)] = self.model.new_bool_var(var_name)

    def _add_hours_per_week_constraint(self) -> None:
        """
        Constraint: Each assignment must be scheduled exactly hours_per_week times.

        From spec: "a matter must be teached in a class, for a fixed number of hours in a week"
        """
        for assignment in self.data.assignments:
            hours_vars = [
                self.x[(assignment.id, day, hour)]
                for day in range(DAYS_OF_WEEK)
                for hour in range(1, HOURS_PER_DAY + 1)
            ]
            self.model.add(sum(hours_vars) == assignment.hours_per_week)

    def _add_teacher_no_overlap_constraint(self) -> None:
        """
        Constraint: A teacher cannot teach two classes at the same time.

        From spec: "a teacher cannot work in two classes in the same schedule slot"
        """
        for _, assignments in self.assignments_by_teacher.items():
            if len(assignments) <= 1:
                continue

            for day in range(DAYS_OF_WEEK):
                for hour in range(1, HOURS_PER_DAY + 1):
                    # At most one assignment for this teacher at this time
                    slot_vars = [self.x[(assignment.id, day, hour)] for assignment in assignments]
                    self.model.add(sum(slot_vars) <= 1)

    def _add_class_no_overlap_constraint(self) -> None:
        """
        Constraint: A class can only have one lesson at a time.

        From spec: "in a class, there can be only one teacher at time, teaching one matter"
        """
        for class_id, assignments in self.assignments_by_class.items():
            if len(assignments) <= 1:
                continue

            for day in range(DAYS_OF_WEEK):
                for hour in range(1, HOURS_PER_DAY + 1):
                    # At most one assignment for this class at this time
                    slot_vars = [self.x[(assignment.id, day, hour)] for assignment in assignments]
                    self.model.add(sum(slot_vars) <= 1)

    def _add_teacher_unavailability_constraint(self) -> None:
        """
        Constraint: Teachers cannot be scheduled during their unavailability slots.

        This handles teachers working at multiple schools.
        """
        for teacher_id, day, hour in self.unavailable:
            if teacher_id not in self.assignments_by_teacher:
                continue

            for assignment in self.assignments_by_teacher[teacher_id]:
                # Force this slot to be 0 (not scheduled)
                self.model.add(self.x[(assignment.id, day, hour)] == 0)

    def _add_fixed_lessons_constraint(self) -> None:
        """Keep user-configured class lessons in their exact weekly slots."""
        for fixed_lesson in self.data.fixed_lessons:
            self.model.add(
                self.x[
                    (
                        fixed_lesson.assignment_id,
                        fixed_lesson.day_of_week,
                        fixed_lesson.hour_slot,
                    )
                ]
                == 1
            )

    def _add_daily_teacher_workload_constraint(self) -> None:
        """Enforce workday distribution and legal daily teaching-hour limits."""
        for teacher_id, assignments in self.assignments_by_teacher.items():
            teacher = next(teacher for teacher in self.data.teachers if teacher.id == teacher_id)
            fully_unavailable = self.fully_unavailable_by_teacher[teacher_id]

            # A legacy contradictory record is treated like a hard full-day block:
            # hard unavailability takes precedence over a flexible request.
            uses_flexible_day = teacher.prefers_day_off and not fully_unavailable
            for day in range(DAYS_OF_WEEK):
                day_hours = [
                    self.x[(assignment.id, day, hour)]
                    for assignment in assignments
                    for hour in range(1, HOURS_PER_DAY + 1)
                ]
                if not uses_flexible_day:
                    if day not in fully_unavailable:
                        self.model.add_linear_expression_in_domain(
                            sum(day_hours), cp_model.Domain.from_values([2, 3, 4, 5])
                        )
                    continue

                works_on_day = self.model.new_bool_var(
                    f"teacher_{teacher_id}_works_day_{day}"
                )
                self.model.add(sum(day_hours) >= 2 * works_on_day)
                self.model.add(sum(day_hours) <= 5 * works_on_day)
                self.works_on_day[(teacher_id, day)] = works_on_day

            if uses_flexible_day:
                teacher_workdays = [
                    self.works_on_day[(teacher_id, day)] for day in range(DAYS_OF_WEEK)
                ]
                self.model.add(sum(teacher_workdays) <= DAYS_OF_WEEK - 1)

    def _add_at_least_twice_per_week_constraint(self) -> None:
        """
        Constraint: Assignment must be split across at least 2 different days.

        This is achieved by limiting each day to at most (total_hours - 1) hours,
        forcing the lessons to span multiple days.
        """
        for assignment in self.data.assignments:
            if assignment.id in self.at_least_twice_per_week_assignments:
                for day in range(DAYS_OF_WEEK):
                    day_vars = [
                        self.x[(assignment.id, day, hour)] for hour in range(1, HOURS_PER_DAY + 1)
                    ]
                    self.model.add(sum(day_vars) <= assignment.hours_per_week - 1)

    def _add_at_least_one_lesson_of_three_hours_per_week_constraint(self) -> None:
        """
        Constraint: At least one lesson must be 3 consecutive hours in a week.

        For each assignment with this requirement, we create boolean variables
        for each possible 3-hour block (day, start_hour), and require at least one
        to be fully scheduled.
        """
        for assignment_id in self.lesson_of_three_hours_per_week_assignments:
            # Create auxiliary variables for each possible 3-hour block
            block_indicators = []
            for day in range(DAYS_OF_WEEK):
                # Possible start hours for a 3-hour block: 1, 2, 3, 4 (ending at 3, 4, 5, 6)
                for start_hour in range(1, HOURS_PER_DAY - 2 + 1):
                    # Create indicator variable: 1 if this 3-hour block is fully scheduled
                    block_var = self.model.new_bool_var(
                        f"block3_a{assignment_id}_d{day}_h{start_hour}"
                    )
                    block_indicators.append(block_var)

                    # Get the 3 consecutive hour variables
                    hour_vars = [
                        self.x[(assignment_id, day, hour)]
                        for hour in range(start_hour, start_hour + 3)
                    ]

                    # If block_var is 1, all 3 hours must be scheduled
                    # block_var => (h1 AND h2 AND h3), equivalent to: block_var <= min(h1, h2, h3)
                    # In CP-SAT: if block_var is true, each hour var must be true
                    for hv in hour_vars:
                        self.model.add(hv >= block_var)

            # At least one 3-hour block must exist
            if block_indicators:
                self.model.add(sum(block_indicators) >= 1)

    def _add_at_least_one_lesson_of_two_hours_per_week_constraint(self) -> None:
        """
        Constraint: At least one lesson must be 2 consecutive hours in a week.

        Similar to the 3-hour constraint but for 2-hour blocks.
        """
        for assignment_id in self.lesson_of_two_hours_per_week_assignments:
            # Create auxiliary variables for each possible 2-hour block
            block_indicators = []
            for day in range(DAYS_OF_WEEK):
                # Possible start hours for a 2-hour block: 1, 2, 3, 4, 5 (ending at 2, 3, 4, 5, 6)
                for start_hour in range(1, HOURS_PER_DAY):
                    # Create indicator variable: 1 if this 2-hour block is fully scheduled
                    block_var = self.model.new_bool_var(
                        f"block2_a{assignment_id}_d{day}_h{start_hour}"
                    )
                    block_indicators.append(block_var)

                    # Get the 2 consecutive hour variables
                    hour_vars = [
                        self.x[(assignment_id, day, hour)]
                        for hour in range(start_hour, start_hour + 2)
                    ]

                    # If block_var is 1, both hours must be scheduled
                    for hv in hour_vars:
                        self.model.add(hv >= block_var)

            # At least one 2-hour block must exist
            if block_indicators:
                self.model.add(sum(block_indicators) >= 1)

    def _add_daily_assignment_cap_constraint(self) -> None:
        """
        Constraint: a matter-class assignment occupies at most its daily cap of
        hours in a single day - MAX_DAILY_ASSIGNMENT_HOURS unless the assignment
        declares a tighter one.

        The cap is on the daily total, not on the length of a run: a two-hour
        cap rejects two consecutive hours plus a third one later the same day.
        It subsumes the previous 4-consecutive-hours rule.
        """
        for assignment in self.data.assignments:
            cap = self.daily_cap_by_assignment[assignment.id]
            for day in range(DAYS_OF_WEEK):
                day_vars = [
                    self.x[(assignment.id, day, hour)]
                    for hour in range(1, HOURS_PER_DAY + 1)
                ]
                self.model.add(sum(day_vars) <= cap)

    def _teacher_day_hours(
        self, assignments: list[ClassMatterAssignment], day: int, hour: int
    ) -> Any:
        """0/1 expression: this teacher teaches at (day, hour)."""
        return sum(self.x[(assignment.id, day, hour)] for assignment in assignments)

    def _add_objective(self) -> None:
        """
        Minimise a single weighted sum of named penalties.

        Every term applies to every teacher, whatever their preference: a teacher
        with no preference used to contribute nothing at all, which left the
        solver free to return the first legal timetable it stumbled on.
        """
        terms: list[tuple[int, cp_model.IntVar]] = []

        self._add_time_preference_terms(terms)
        self._add_class_block_terms(terms)
        self._add_gap_terms(terms)
        self._add_long_run_terms(terms)
        self._add_daily_balance_terms(terms)

        objective_terms = [
            weight * variable for weight, variable in terms if weight
        ]
        if objective_terms:
            self.model.minimize(sum(objective_terms))

    def _add_time_preference_terms(
        self, terms: list[tuple[int, cp_model.IntVar]]
    ) -> None:
        """Penalise slots away from the teacher's preferred end of the day."""
        for teacher_id, assignments in self.assignments_by_teacher.items():
            preference = self.preference_by_teacher.get(teacher_id)
            if preference == SchedulePreference.EARLY.value:
                def coefficient(hour: int) -> int:
                    return hour - 1
            elif preference == SchedulePreference.LATE.value:
                def coefficient(hour: int) -> int:
                    return HOURS_PER_DAY - hour
            else:
                continue

            for assignment in assignments:
                for day in range(DAYS_OF_WEEK):
                    for hour in range(1, HOURS_PER_DAY + 1):
                        weight = W_TIME_PREFERENCE * coefficient(hour)
                        if weight:
                            terms.append((weight, self.x[(assignment.id, day, hour)]))

    def _add_class_block_terms(
        self, terms: list[tuple[int, cp_model.IntVar]]
    ) -> None:
        """
        Penalise every start of a run of consecutive hours a teacher spends in
        one class.

        Counting starts rather than transitions between class pairs keeps this
        linear in classes instead of quadratic, and catches both alternation
        between classes and the same class picked up again after a break.
        """
        for teacher_id, by_class in self.assignments_by_teacher_class.items():
            for class_id, assignments in by_class.items():
                for day in range(DAYS_OF_WEEK):
                    for hour in range(1, HOURS_PER_DAY + 1):
                        here = self._teacher_day_hours(assignments, day, hour)
                        previous = (
                            self._teacher_day_hours(assignments, day, hour - 1)
                            if hour > 1
                            else 0
                        )
                        start = self.model.new_bool_var(
                            f"start_t{teacher_id}_c{class_id}_d{day}_h{hour}"
                        )
                        self.model.add(start >= here - previous)
                        terms.append((W_CLASS_BLOCK, start))

    def _add_gap_terms(self, terms: list[tuple[int, cp_model.IntVar]]) -> None:
        """
        Penalise free slots sandwiched between lessons of the same teacher.

        A day long enough to be worth breaking gets an allowance of one gap hour;
        every hour past it costs more than the rest of the objective can gain in
        a whole week, so a second one is never worth buying. Short days get no
        allowance at all, and that is where the proportionality between workload
        and gaps comes from: a teacher with few hours only has short days, so the
        model gives them no gaps without ever mentioning their weekly total.

        Slots the teacher is unavailable for are not gaps. They are not at school
        and are not waiting, so only the free time in which they could have been
        teaching counts.
        """
        for teacher_id, assignments in self.assignments_by_teacher.items():
            preference = self.preference_by_teacher.get(teacher_id)

            for day in range(DAYS_OF_WEEK):
                occupied = {
                    hour: self._teacher_day_hours(assignments, day, hour)
                    for hour in range(1, HOURS_PER_DAY + 1)
                }
                # Monotone chains: before[h] is 1 iff a lesson precedes hour h.
                before = {
                    hour: self.model.new_bool_var(f"before_t{teacher_id}_d{day}_h{hour}")
                    for hour in range(1, HOURS_PER_DAY + 1)
                }
                after = {
                    hour: self.model.new_bool_var(f"after_t{teacher_id}_d{day}_h{hour}")
                    for hour in range(1, HOURS_PER_DAY + 1)
                }
                self.model.add(before[1] == 0)
                self.model.add(after[HOURS_PER_DAY] == 0)
                for hour in range(2, HOURS_PER_DAY + 1):
                    self.model.add(before[hour] >= before[hour - 1])
                    self.model.add(before[hour] >= occupied[hour - 1])
                for hour in range(HOURS_PER_DAY - 1, 0, -1):
                    self.model.add(after[hour] >= after[hour + 1])
                    self.model.add(after[hour] >= occupied[hour + 1])

                day_gaps = []
                for hour in range(1, HOURS_PER_DAY + 1):
                    if (teacher_id, day, hour) in self.unavailable:
                        continue
                    gap = self.model.new_bool_var(f"gap_t{teacher_id}_d{day}_h{hour}")
                    self.model.add(
                        gap >= before[hour] + after[hour] - occupied[hour] - 1
                    )
                    day_gaps.append(gap)
                if not day_gaps:
                    continue

                # The allowance is read off the day's load, not its layout, so it
                # is not circular: a four-hour day earns it whether it is laid
                # out as one run or as two blocks, and the comparison decides.
                load = sum(occupied.values())
                allowance = self.model.new_bool_var(f"allow_t{teacher_id}_d{day}")
                self.model.add(load >= LONG_RUN_WINDOW).only_enforce_if(allowance)
                self.model.add(load < LONG_RUN_WINDOW).only_enforce_if(
                    allowance.negated()
                )

                excess = self.model.new_int_var(
                    0, HOURS_PER_DAY, f"excess_gap_t{teacher_id}_d{day}"
                )
                self.model.add(excess >= sum(day_gaps) - allowance)
                terms.append((W_EXCESS_GAP, excess))

                self._add_break_day_term(
                    terms, teacher_id, day, preference, day_gaps, allowance
                )

    def _add_break_day_term(
        self,
        terms: list[tuple[int, cp_model.IntVar]],
        teacher_id: int,
        day: int,
        preference: str | None,
        day_gaps: list[cp_model.IntVar],
        allowance: cp_model.IntVar,
    ) -> None:
        """
        Charge the one break a day is allowed, according to the teacher's gap
        preference.

        The preference acts on how many days of the week carry their break, not
        on how deep a single day is cut: no preference can exceed a day's
        allowance, so "more gaps" is only ever expressible as "more days with the
        one gap". Summed over the week, that is exactly the weekly reading
        teachers give these preferences.
        """
        break_day = self.model.new_bool_var(f"break_t{teacher_id}_d{day}")
        self.model.add(sum(day_gaps) >= 1).only_enforce_if(break_day)
        self.model.add(sum(day_gaps) == 0).only_enforce_if(break_day.negated())

        if preference == SchedulePreference.MAXIMIZE_GAPS.value:
            # Anchoring to the allowance does double duty: on a short day the
            # term is identically zero, so the preference never pushes towards a
            # gap that would cost W_EXCESS_GAP.
            missed = self.model.new_bool_var(f"missed_break_t{teacher_id}_d{day}")
            self.model.add(missed >= allowance - break_day)
            terms.append((W_BREAK_DAY, missed))
            return

        weight = (
            W_BREAK_DAY_STRICT
            if preference == SchedulePreference.MINIMIZE_GAPS.value
            else W_BREAK_DAY
        )
        terms.append((weight, break_day))

    def _add_long_run_terms(self, terms: list[tuple[int, cp_model.IntVar]]) -> None:
        """
        Penalise every window of LONG_RUN_WINDOW consecutive teaching hours.

        A five-hour run contains two such windows and so costs twice a four-hour
        run, which gives the "three great, four ok, five too many" ordering
        without a second term.
        """
        for teacher_id, assignments in self.assignments_by_teacher.items():
            for day in range(DAYS_OF_WEEK):
                for start_hour in range(1, HOURS_PER_DAY - LONG_RUN_WINDOW + 2):
                    window = [
                        self.x[(assignment.id, day, hour)]
                        for assignment in assignments
                        for hour in range(start_hour, start_hour + LONG_RUN_WINDOW)
                    ]
                    run = self.model.new_bool_var(
                        f"run_t{teacher_id}_d{day}_h{start_hour}"
                    )
                    self.model.add(run >= sum(window) - (LONG_RUN_WINDOW - 1))
                    terms.append((W_LONG_RUN, run))

    def _add_daily_balance_terms(
        self, terms: list[tuple[int, cp_model.IntVar]]
    ) -> None:
        """
        Pull each teaching day towards a band derived from the teacher's own
        weekly hours spread over their eligible weekdays.

        Deriving the band instead of hardcoding "three or four hours" makes it
        adapt on its own to reduced hours and to teachers who also work at
        another school.
        """
        for teacher_id, assignments in self.assignments_by_teacher.items():
            workdays = self.eligible_workdays.get(teacher_id, 0)
            if workdays <= 0:
                continue

            total = sum(assignment.hours_per_week for assignment in assignments)
            low, high = daily_band(total, workdays)
            fully_unavailable = self.fully_unavailable_by_teacher[teacher_id]

            for day in range(DAYS_OF_WEEK):
                if day in fully_unavailable:
                    continue

                load = sum(
                    self._teacher_day_hours(assignments, day, hour)
                    for hour in range(1, HOURS_PER_DAY + 1)
                )
                deviation = self.model.new_int_var(
                    0, HOURS_PER_DAY, f"balance_t{teacher_id}_d{day}"
                )
                self.model.add(deviation >= load - high)

                works = self.works_on_day.get((teacher_id, day))
                if works is None:
                    self.model.add(deviation >= low - load)
                else:
                    # A solver-selected free day is not a day below the band.
                    self.model.add(deviation >= low * works - load)
                terms.append((W_DAILY_BALANCE, deviation))

    def build_model(self) -> None:
        """Build the complete CP model with all variables and constraints."""
        self._create_variables()

        # Hard constraints
        self._add_hours_per_week_constraint()
        self._add_teacher_no_overlap_constraint()
        self._add_class_no_overlap_constraint()
        self._add_teacher_unavailability_constraint()
        self._add_fixed_lessons_constraint()
        self._add_daily_teacher_workload_constraint()
        self._add_daily_assignment_cap_constraint()

        # Matter requirement constraints
        self._add_at_least_twice_per_week_constraint()
        self._add_at_least_one_lesson_of_three_hours_per_week_constraint()
        self._add_at_least_one_lesson_of_two_hours_per_week_constraint()

        # Soft constraints (objectives)
        self._add_objective()

    def solve(self, time_limit_seconds: float = 120.0) -> GeneratedSchedule:
        """
        Solve the scheduling problem and return the generated schedule.

        Args:
            time_limit_seconds: Maximum time to spend solving.

        Returns:
            GeneratedSchedule with the solution or empty if infeasible.
        """
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = time_limit_seconds
        solver.parameters.num_search_workers = 16

        status = solver.Solve(self.model)

        schedule = GeneratedSchedule()
        schedule.solve_time_seconds = solver.WallTime()

        status_names = {
            cp_model.OPTIMAL: "OPTIMAL",
            cp_model.FEASIBLE: "FEASIBLE",
            cp_model.INFEASIBLE: "INFEASIBLE",
            cp_model.MODEL_INVALID: "MODEL_INVALID",
            cp_model.UNKNOWN: "UNKNOWN",
        }
        schedule.status = status_names.get(status, "UNKNOWN")

        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            schedule.slots = self._extract_solution(solver)
            schedule.quality = compute_quality_metrics(
                schedule.slots, self.eligible_workdays, self.unavailable
            )

        return schedule

    def _extract_solution(self, solver: cp_model.CpSolver) -> list[ScheduleSlot]:
        """Extract the schedule slots from the solver solution."""
        slots = []

        for assignment in self.data.assignments:
            for day in range(DAYS_OF_WEEK):
                for hour in range(1, HOURS_PER_DAY + 1):
                    if solver.Value(self.x[(assignment.id, day, hour)]) == 1:
                        slot = ScheduleSlot(
                            day=day,
                            hour=hour,
                            class_id=assignment.class_id,
                            class_name=assignment.school_class.name,
                            teacher_id=assignment.teacher_id,
                            teacher_name=f"{assignment.teacher.first_name} {assignment.teacher.last_name}",
                            matter_id=assignment.matter_id,
                            matter_name=assignment.matter.name,
                            assignment_id=assignment.id,
                        )
                        slots.append(slot)

        return slots


def find_teachers_with_unsatisfiable_daily_workload(
    data: SchedulingData, time_limit_seconds: float = 5.0
) -> list[Teacher]:
    """
    Identify teachers whose own assignments can never satisfy the legal daily
    workload constraint (0, or 2-5 hours/day), independently of every other
    teacher or class.

    This solves each teacher's assignments, unavailabilities, and fixed lessons
    in isolation. Adding more teachers or classes to the full joint model can
    only add constraints (e.g. a class slot already used by another matter),
    never relax them. So a teacher whose isolated model is infeasible is
    guaranteed infeasible in the full schedule too - this lets a single
    unsatisfiable teacher be reported clearly instead of the whole generation
    failing with an opaque INFEASIBLE status.

    A common cause: a matter requiring "at least twice per week" forces its
    hours below a legal daily minimum (e.g. a lone 2-hour/week assignment
    splits into two 1-hour days) with no other assignment on those days to
    reach the required minimum.
    """
    assignments_by_teacher: dict[int, list[ClassMatterAssignment]] = {}
    for assignment in data.assignments:
        assignments_by_teacher.setdefault(assignment.teacher_id, []).append(assignment)

    unsatisfiable: list[Teacher] = []
    for teacher in data.teachers:
        assignments = assignments_by_teacher.get(teacher.id)
        if not assignments:
            continue

        assignment_ids = {a.id for a in assignments}
        classes_by_id = {a.school_class.id: a.school_class for a in assignments}
        sub_data = SchedulingData(
            teachers=[teacher],
            classes=list(classes_by_id.values()),
            assignments=assignments,
            unavailabilities=[
                u for u in data.unavailabilities if u.teacher_id == teacher.id
            ],
            fixed_lessons=[
                f for f in data.fixed_lessons if f.assignment_id in assignment_ids
            ],
        )
        generator = ScheduleGenerator(sub_data)
        generator.build_model()
        result = generator.solve(time_limit_seconds=time_limit_seconds)
        if result.status not in ("OPTIMAL", "FEASIBLE"):
            unsatisfiable.append(teacher)

    return unsatisfiable


def generate_schedule(
    db: Session,
    workspace_id: int,
    time_limit_seconds: float = 120.0,
    save_to_db: bool = True,
    nickname: str | None = None,
) -> GeneratedSchedule:
    """
    Main entry point for schedule generation.

    Fetches data from the database, builds the constraint model,
    solves it, and optionally saves the result to the database.

    Args:
        db: SQLAlchemy database session
        workspace_id: Workspace owner for the generated schedule
        time_limit_seconds: Maximum solving time
        save_to_db: Whether to save the schedule to the database
        nickname: Optional user-friendly name for the schedule

    Returns:
        GeneratedSchedule containing the solution
    """
    # Fetch all data from database
    data = fetch_scheduling_data(db, workspace_id=workspace_id)

    if not data.assignments:
        schedule = GeneratedSchedule()
        schedule.status = "NO_DATA"
        return schedule

    # Build and solve the model
    generator = ScheduleGenerator(data)
    generator.build_model()

    schedule = generator.solve(time_limit_seconds)

    # Save to database if requested and successful
    if save_to_db and schedule.status in ("OPTIMAL", "FEASIBLE"):
        save_schedule_to_db(db, workspace_id, schedule, nickname)

    return schedule


def save_schedule_to_db(
    db: Session,
    workspace_id: int,
    schedule: GeneratedSchedule,
    nickname: str | None = None,
) -> SavedSchedule:
    """
    Save a generated schedule to the database.

    Args:
        db: SQLAlchemy database session
        workspace_id: Workspace owner for the schedule
        schedule: The generated schedule to save
        nickname: Optional user-friendly name

    Returns:
        The saved schedule model instance
    """
    # Generate name from timestamp
    name = datetime.now().strftime("Schedule %Y-%m-%d %H:%M:%S")

    # Get schedule data as JSON string (only the schedule part, not metadata)
    schedule_dict = schedule.to_dict()
    schedule_data_json = json.dumps(schedule_dict["schedule"])

    saved_schedule = SavedSchedule(
        workspace_id=workspace_id,
        name=name,
        nickname=nickname,
        status=schedule.status,
        solve_time_seconds=schedule.solve_time_seconds,
        total_slots=len(schedule.slots),
        schedule_data=schedule_data_json,
    )

    db.add(saved_schedule)
    db.commit()
    db.refresh(saved_schedule)

    return saved_schedule
