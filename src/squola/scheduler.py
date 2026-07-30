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
    SchoolClass,
    Teacher,
    TeacherBlacklistedSlot,
    SchedulePreference,
    SavedSchedule,
    MatterRequirements,
)


# Schedule constants
DAYS_OF_WEEK = 5  # Monday to Friday (0-4)
HOURS_PER_DAY = 6  # 8:00 to 14:00 (slots 1-6)
DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
HOUR_LABELS = ["08:00-09:00", "09:00-10:00", "10:00-11:00", "11:00-12:00", "12:00-13:00", "13:00-14:00"]


@dataclass
class SchedulingData:
    """Data container for all scheduling-related information from the database."""
    
    # Core entities
    teachers: list[Teacher] = field(default_factory=list)
    classes: list[SchoolClass] = field(default_factory=list)
    assignments: list[ClassMatterAssignment] = field(default_factory=list)
    
    # Constraints data
    blacklisted_slots: list[TeacherBlacklistedSlot] = field(default_factory=list)
    
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
    
    def to_dict(self) -> dict[str, Any]:
        """Convert schedule to dictionary for JSON serialization."""
        return {
            "metadata": {
                "status": self.status,
                "solve_time_seconds": self.solve_time_seconds,
                "generated_at": self.generated_at,
                "total_slots": len(self.slots),
            },
            "schedule": {
                "by_class": self._group_by_class(),
                "by_teacher": self._group_by_teacher(),
                "by_day": self._group_by_day(),
            }
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
            result[class_name].sort(key=lambda x: (DAY_NAMES.index(x["day"]), HOUR_LABELS.index(x["hour"])))
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
            result[teacher_name].sort(key=lambda x: (DAY_NAMES.index(x["day"]), HOUR_LABELS.index(x["hour"])))
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


def fetch_scheduling_data(db: Session) -> SchedulingData:
    """
    Fetch all necessary data from the database for scheduling.
    
    This includes:
    - All teachers with their blacklisted slots
    - All classes
    - All class-matter-teacher assignments
    """
    data = SchedulingData()
    
    # Fetch teachers with eager loading of blacklisted slots
    data.teachers = list(
        db.query(Teacher)
        .options(joinedload(Teacher.blacklisted_slots))
        .all()
    )
    
    # Fetch all classes
    data.classes = list(db.query(SchoolClass).all())
    
    # Fetch all assignments with eager loading of related entities
    data.assignments = list(
        db.query(ClassMatterAssignment)
        .options(
            joinedload(ClassMatterAssignment.teacher),
            joinedload(ClassMatterAssignment.school_class),
            joinedload(ClassMatterAssignment.matter),
        )
        .all()
    )
    
    # Fetch all blacklisted slots
    data.blacklisted_slots = list(db.query(TeacherBlacklistedSlot).all())
    
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
        
        # Blacklisted slots by teacher: (teacher_id, day, hour) -> True
        self.blacklisted: set[tuple[int, int, int]] = set()
        for slot in self.data.blacklisted_slots:
            self.blacklisted.add((slot.teacher_id, slot.day_of_week, slot.hour_slot))

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
                    slot_vars = [
                        self.x[(assignment.id, day, hour)]
                        for assignment in assignments
                    ]
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
                    slot_vars = [
                        self.x[(assignment.id, day, hour)]
                        for assignment in assignments
                    ]
                    self.model.add(sum(slot_vars) <= 1)
    
    def _add_teacher_blacklist_constraint(self) -> None:
        """
        Constraint: Teachers cannot be scheduled during their blacklisted slots.
        
        This handles teachers working at multiple schools.
        """
        for (teacher_id, day, hour) in self.blacklisted:
            if teacher_id not in self.assignments_by_teacher:
                continue
            
            for assignment in self.assignments_by_teacher[teacher_id]:
                # Force this slot to be 0 (not scheduled)
                self.model.add(self.x[(assignment.id, day, hour)] == 0)
    
    def _add_max_hours_per_day_constraint(self, max_hours: int = HOURS_PER_DAY) -> None:
        """
        Soft constraint: Limit hours per day for teachers to avoid overload.
        """
        for _, assignments in self.assignments_by_teacher.items():
            for day in range(DAYS_OF_WEEK):
                day_hours = [
                    self.x[(assignment.id, day, hour)]
                    for assignment in assignments
                    for hour in range(1, HOURS_PER_DAY + 1)
                ]
                self.model.add(sum(day_hours) <= max_hours)

    def _add_at_least_twice_per_week_constraint(self) -> None:
        """
        Constraint: Assignment must be split across at least 2 different days.
        
        This is achieved by limiting each day to at most (total_hours - 1) hours,
        forcing the lessons to span multiple days.
        """
        for assignment_id in self.at_least_twice_per_week_assignments:
            for day in range(DAYS_OF_WEEK):
                day_vars = [
                    self.x[(assignment_id, day, hour)]
                    for hour in range(1, HOURS_PER_DAY + 1)
                ]
                self.model.add(sum(day_vars) <= 1)

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

    def _add_at_most_three_hours_per_single_lesson_constraint(self) -> None:
        for assignment in self.data.assignments:
            for day in range(DAYS_OF_WEEK):
                for start_hour in range(1, HOURS_PER_DAY - 3 + 1):
                    block_vars = [
                        self.x[(assignment.id, day, hour)]
                        # the block of 4 consecutive hours is needed to exclude possibility of 4-hour lessons
                        for hour in range(start_hour, start_hour + 4)
                    ]
                    self.model.add(sum(block_vars) <= 3)
    
    def _add_preference_objectives(self) -> None:
        """
        Add soft constraints based on teacher preferences.
        
        Preferences are added as objectives to optimize, not hard constraints.
        """
        objective_terms = []
        
        for teacher in self.data.teachers:
            if teacher.id not in self.assignments_by_teacher:
                continue
            
            assignments = self.assignments_by_teacher[teacher.id]
            preference = teacher.schedule_preference
            
            if preference == SchedulePreference.EARLY.value:
                # Prefer early hours: minimize hour index * scheduled
                for assignment in assignments:
                    for day in range(DAYS_OF_WEEK):
                        for hour in range(1, HOURS_PER_DAY + 1):
                            # Higher penalty for later hours
                            objective_terms.append(hour * self.x[(assignment.id, day, hour)])
            
            elif preference == SchedulePreference.LATE.value:
                # Prefer late hours: minimize (max_hour - hour) * scheduled
                for assignment in assignments:
                    for day in range(DAYS_OF_WEEK):
                        for hour in range(1, HOURS_PER_DAY + 1):
                            # Higher penalty for earlier hours
                            objective_terms.append(
                                (HOURS_PER_DAY + 1 - hour) * self.x[(assignment.id, day, hour)]
                            )
            
            elif preference == SchedulePreference.MINIMIZE_GAPS.value:
                # Minimize gaps: use auxiliary variables to track gaps
                # Simplified: prefer consecutive hours by penalizing spread
                self._add_minimize_gaps_for_teacher(teacher.id, assignments, objective_terms)
            
            elif preference == SchedulePreference.MAXIMIZE_GAPS.value:
                # Maximize gaps: opposite of minimize gaps
                self._add_maximize_gaps_for_teacher(teacher.id, assignments, objective_terms)
        
        if objective_terms:
            self.model.minimize(sum(objective_terms))
    
    def _add_minimize_gaps_for_teacher(
        self,
        teacher_id: int,
        assignments: list[ClassMatterAssignment],
        objective_terms: list
    ) -> None:
        """Add gap minimization for a teacher (group lessons together)."""
        for day in range(DAYS_OF_WEEK):
            # Penalize using non-consecutive hours
            for hour in range(1, HOURS_PER_DAY + 1):
                for assignment in assignments:
                    # Penalty increases with distance from first hour
                    objective_terms.append(
                        (hour - 1) * self.x[(assignment.id, day, hour)]
                    )
    
    def _add_maximize_gaps_for_teacher(
        self,
        teacher_id: int,
        assignments: list[ClassMatterAssignment],
        objective_terms: list
    ) -> None:
        """Add gap maximization for a teacher (spread lessons out)."""
        for day in range(DAYS_OF_WEEK):
            # Reward spreading lessons across different hours
            for hour in range(1, HOURS_PER_DAY + 1):
                for assignment in assignments:
                    # Penalty for middle hours (prefer extremes)
                    middle = (HOURS_PER_DAY + 1) / 2
                    distance_from_middle = abs(hour - middle)
                    # Invert: penalize being close to middle (coefficient must be computed first)
                    coefficient = int(middle - distance_from_middle)
                    objective_terms.append(
                        coefficient * self.x[(assignment.id, day, hour)]
                    )
    
    def build_model(self) -> None:
        """Build the complete CP model with all variables and constraints."""
        self._create_variables()
        
        # Hard constraints
        self._add_hours_per_week_constraint()
        self._add_teacher_no_overlap_constraint()
        self._add_class_no_overlap_constraint()
        self._add_teacher_blacklist_constraint()
        self._add_max_hours_per_day_constraint()
        self._add_at_most_three_hours_per_single_lesson_constraint()
        
        # Matter requirement constraints
        self._add_at_least_twice_per_week_constraint()
        self._add_at_least_one_lesson_of_three_hours_per_week_constraint()
        self._add_at_least_one_lesson_of_two_hours_per_week_constraint()
        
        # Soft constraints (objectives)
        self._add_preference_objectives()
    
    def solve(self, time_limit_seconds: float = 60.0) -> GeneratedSchedule:
        """
        Solve the scheduling problem and return the generated schedule.
        
        Args:
            time_limit_seconds: Maximum time to spend solving.
            
        Returns:
            GeneratedSchedule with the solution or empty if infeasible.
        """
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = time_limit_seconds
        
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


def generate_schedule(
    db: Session,
    time_limit_seconds: float = 60.0,
    save_to_db: bool = True,
    nickname: str | None = None,
) -> GeneratedSchedule:
    """
    Main entry point for schedule generation.
    
    Fetches data from the database, builds the constraint model,
    solves it, and optionally saves the result to the database.
    
    Args:
        db: SQLAlchemy database session
        time_limit_seconds: Maximum solving time
        save_to_db: Whether to save the schedule to the database
        nickname: Optional user-friendly name for the schedule
        
    Returns:
        GeneratedSchedule containing the solution
    """
    # Fetch all data from database
    data = fetch_scheduling_data(db)
    
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
        save_schedule_to_db(db, schedule, nickname)
    
    return schedule


def save_schedule_to_db(
    db: Session,
    schedule: GeneratedSchedule,
    nickname: str | None = None,
) -> SavedSchedule:
    """
    Save a generated schedule to the database.
    
    Args:
        db: SQLAlchemy database session
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
