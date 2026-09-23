"""
Manual swaps on a saved timetable.

A swap is defined by a lesson (teacher T, slot s1) and a second slot s2. Its
chain is the connected component of T in the teacher-class graph restricted to
the lessons of s1 and s2: every node has degree at most two (one lesson per
slot), so the component is a path or a cycle, and moving each of its lessons to
the other slot keeps every class-matter weekly count unchanged. The chain is
forced by the timetable, never chosen. See docs/cambi.md.
"""

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any

from squola.models import ClassMatterAssignment, MatterRequirements, Teacher
from squola.scheduler import (
    DAY_NAMES,
    DAYS_OF_WEEK,
    HOUR_LABELS,
    HOURS_PER_DAY,
    LEGAL_DAILY_TEACHING_HOURS,
    LESSON_LENGTH_HOURS,
    WORKDAY_TEACHING_HOURS,
    ScheduleSlot,
    SchedulingData,
    compute_quality_metrics,
    fully_unavailable_days,
    resolve_daily_cap,
    uses_flexible_day_off,
)

Slot = tuple[int, int]  # (day 0-4, hour 1-6)
ALL_SLOTS: list[Slot] = [
    (day, hour) for day in range(DAYS_OF_WEEK) for hour in range(1, HOURS_PER_DAY + 1)
]
WARNING_METRICS = ("excess_gap_hours", "long_runs")


class SwapError(ValueError):
    """A swap that cannot be applied."""


@dataclass(frozen=True)
class Lesson:
    assignment_id: int
    day: int
    hour: int

    @property
    def slot(self) -> Slot:
        return (self.day, self.hour)


@dataclass
class SwapContext:
    """Current workspace data the swaps are checked against."""

    data: SchedulingData
    assignments: dict[int, ClassMatterAssignment] = field(init=False)
    teachers: dict[int, Teacher] = field(init=False)
    assignments_by_teacher: dict[int, list[ClassMatterAssignment]] = field(init=False)
    unavailable: set[tuple[int, int, int]] = field(init=False)
    fully_unavailable: dict[int, set[int]] = field(init=False)
    fixed: set[tuple[int, int, int]] = field(init=False)

    def __post_init__(self) -> None:
        data = self.data
        self.assignments = {a.id: a for a in data.assignments}
        self.teachers = {t.id: t for t in data.teachers}
        self.assignments_by_teacher = defaultdict(list)
        for assignment in data.assignments:
            self.assignments_by_teacher[assignment.teacher_id].append(assignment)
        self.unavailable = {
            (u.teacher_id, u.day_of_week, u.hour_slot) for u in data.unavailabilities
        }
        self.fully_unavailable = {
            t.id: fully_unavailable_days(data.unavailabilities, t.id) for t in data.teachers
        }
        self.fixed = {
            (f.assignment_id, f.day_of_week, f.hour_slot) for f in data.fixed_lessons
        }

    def teacher_of(self, lesson: Lesson) -> int:
        return self.assignments[lesson.assignment_id].teacher_id

    def class_of(self, lesson: Lesson) -> int:
        return self.assignments[lesson.assignment_id].class_id

    def teacher_name(self, teacher_id: int) -> str:
        teacher = self.teachers[teacher_id]
        return f"{teacher.first_name} {teacher.last_name}"

    def to_schedule_slot(self, lesson: Lesson) -> ScheduleSlot:
        assignment = self.assignments[lesson.assignment_id]
        return ScheduleSlot(
            day=lesson.day,
            hour=lesson.hour,
            class_id=assignment.class_id,
            class_name=assignment.school_class.name,
            teacher_id=assignment.teacher_id,
            teacher_name=self.teacher_name(assignment.teacher_id),
            matter_id=assignment.matter_id,
            matter_name=assignment.matter.name,
            assignment_id=assignment.id,
        )


def load_lessons(
    schedule_data: dict[str, Any], ctx: SwapContext
) -> tuple[list[Lesson], list[dict[str, Any]]]:
    """
    Link the lessons of a saved timetable to the current assignments.

    Timetables saved with ids are linked by assignment id. Older ones are linked
    by (teacher, class, matter) names, and a lesson matching zero or several
    current assignments is returned as unlinked rather than guessed.
    """
    by_names: dict[tuple[str, str, str], list[int]] = defaultdict(list)
    for assignment in ctx.data.assignments:
        key = (
            ctx.teacher_name(assignment.teacher_id),
            assignment.school_class.name,
            assignment.matter.name,
        )
        by_names[key].append(assignment.id)

    lessons: list[Lesson] = []
    unlinked: list[dict[str, Any]] = []
    for class_name, entries in schedule_data.get("by_class", {}).items():
        for entry in entries:
            day = DAY_NAMES.index(entry["day"])
            hour = HOUR_LABELS.index(entry["hour"]) + 1
            if "assignment_id" in entry:
                matches = [entry["assignment_id"]] if entry["assignment_id"] in ctx.assignments else []
            else:
                matches = by_names.get((entry["teacher"], class_name, entry["matter"]), [])
            if len(matches) == 1:
                lessons.append(Lesson(matches[0], day, hour))
            else:
                unlinked.append({
                    "day": day,
                    "hour": hour,
                    "class": class_name,
                    "teacher": entry["teacher"],
                    "matter": entry["matter"],
                })
    return lessons, unlinked


def find_chain(
    lessons: list[Lesson], ctx: SwapContext, teacher_id: int, s1: Slot, s2: Slot
) -> list[Lesson]:
    """The lessons a swap moves, or SwapError when the swap is not admissible."""
    if s1 == s2:
        raise SwapError("the two slots must differ")
    in_slots = [lesson for lesson in lessons if lesson.slot in (s1, s2)]
    start = [l for l in in_slots if l.slot == s1 and ctx.teacher_of(l) == teacher_id]
    if not start:
        raise SwapError("the teacher has no lesson in the selected slot")

    # Grow the component: a lesson pulls in the lessons of its teacher and of
    # its class in either slot.
    chain: set[Lesson] = set()
    frontier = list(start)
    while frontier:
        lesson = frontier.pop()
        if lesson in chain:
            continue
        chain.add(lesson)
        teacher, school_class = ctx.teacher_of(lesson), ctx.class_of(lesson)
        frontier.extend(
            other
            for other in in_slots
            if other not in chain
            and (ctx.teacher_of(other) == teacher or ctx.class_of(other) == school_class)
        )

    by_class: dict[int, dict[Slot, list[int]]] = defaultdict(lambda: {s1: [], s2: []})
    for lesson in chain:
        by_class[ctx.class_of(lesson)][lesson.slot].append(lesson.assignment_id)
        if (lesson.assignment_id, lesson.day, lesson.hour) in ctx.fixed:
            raise SwapError("the chain contains a fixed lesson")
    for per_slot in by_class.values():
        if not per_slot[s1] or not per_slot[s2]:
            raise SwapError("the swap would leave a class without a lesson")
    if all(sorted(per_slot[s1]) == sorted(per_slot[s2]) for per_slot in by_class.values()):
        raise SwapError("the swap has no effect")

    return sorted(chain, key=lambda l: (l.day, l.hour, l.assignment_id))


def apply_chain(lessons: list[Lesson], chain: list[Lesson], s1: Slot, s2: Slot) -> list[Lesson]:
    """Move every lesson of the chain to the other slot."""
    moved = set(chain)
    result = []
    for lesson in lessons:
        if lesson in moved:
            day, hour = s2 if lesson.slot == s1 else s1
            lesson = Lesson(lesson.assignment_id, day, hour)
        result.append(lesson)
    return result


def _longest_run(hours: list[int]) -> int:
    longest = run = 0
    previous = None
    for hour in sorted(set(hours)):
        run = run + 1 if previous is not None and hour == previous + 1 else 1
        longest = max(longest, run)
        previous = hour
    return longest


def count_violations(
    lessons: list[Lesson], ctx: SwapContext, teacher_ids: set[int], days: set[int]
) -> Counter:
    """
    Hard-constraint violations per (rule, entity, day) for the given teachers and
    their assignments. Daily rules are evaluated on `days` only; weekly rules
    use day None. Mirrors the constraints of ScheduleGenerator.
    """
    hours_by_teacher_day: dict[tuple[int, int], list[int]] = defaultdict(list)
    hours_by_assignment_day: dict[tuple[int, int], list[int]] = defaultdict(list)
    for lesson in lessons:
        teacher_id = ctx.teacher_of(lesson)
        if teacher_id in teacher_ids:
            hours_by_teacher_day[(teacher_id, lesson.day)].append(lesson.hour)
            hours_by_assignment_day[(lesson.assignment_id, lesson.day)].append(lesson.hour)

    violations: Counter = Counter()
    for teacher_id in teacher_ids:
        if not ctx.assignments_by_teacher.get(teacher_id):
            continue  # like the generator, which only constrains teachers who teach
        blocked = ctx.fully_unavailable.get(teacher_id, set())
        flexible = uses_flexible_day_off(ctx.teachers[teacher_id], blocked)
        free_days = 0
        for day in range(DAYS_OF_WEEK):
            hours = hours_by_teacher_day.get((teacher_id, day), [])
            free_days += not hours
            if day not in days:
                continue
            violations[("teacher_overlap", teacher_id, day)] = len(hours) - len(set(hours))
            violations[("unavailable", teacher_id, day)] = sum(
                (teacher_id, day, hour) in ctx.unavailable for hour in hours
            )
            # A fully blocked day is already covered by unavailability.
            if day not in blocked:
                allowed = LEGAL_DAILY_TEACHING_HOURS if flexible else WORKDAY_TEACHING_HOURS
                violations[("daily_hours", teacher_id, day)] = len(hours) not in allowed
        if flexible:
            violations[("day_off", teacher_id, None)] = free_days == 0

        for assignment in ctx.assignments_by_teacher.get(teacher_id, []):
            requirements = assignment.requirements or []
            per_day = [
                hours_by_assignment_day.get((assignment.id, day), [])
                for day in range(DAYS_OF_WEEK)
            ]
            cap = resolve_daily_cap(requirements)
            for day in days:
                violations[("daily_cap", assignment.id, day)] = max(0, len(per_day[day]) - cap)
            if MatterRequirements.AT_LEAST_TWICE_PER_WEEK in requirements:
                violations[("at_least_twice_per_week", assignment.id, None)] = sum(
                    len(hours) > assignment.hours_per_week - 1 for hours in per_day
                )
            for requirement, length in LESSON_LENGTH_HOURS.items():
                if requirement in requirements:
                    violations[(requirement.value, assignment.id, None)] = not any(
                        _longest_run(hours) >= length for hours in per_day
                    )
    return +violations  # drop zero counts


def _describe(ctx: SwapContext, rule: str, entity: int, day: int | None) -> str:
    if rule in ("teacher_overlap", "unavailable", "daily_hours", "day_off"):
        who = ctx.teacher_name(entity)
    else:
        assignment = ctx.assignments[entity]
        who = f"{assignment.matter.name} in {assignment.school_class.name}"
    return f"{rule}: {who}" + (f" on {DAY_NAMES[day]}" if day is not None else "")


def _day_quality(
    lessons: list[Lesson], ctx: SwapContext, teacher_id: int, day: int
) -> dict[str, Any]:
    slots = [
        ctx.to_schedule_slot(l)
        for l in lessons
        if l.day == day and ctx.teacher_of(l) == teacher_id
    ]
    return compute_quality_metrics(slots, {}, ctx.unavailable)


def check_swap(
    lessons: list[Lesson], ctx: SwapContext, teacher_id: int, s1: Slot, s2: Slot
) -> tuple[list[Lesson], list[Lesson], list[dict[str, Any]]]:
    """
    Apply a swap if it introduces no hard violation.

    Returns (new lessons, chain, warnings). A violation already present before
    the swap and not worsened by it does not reject the swap.
    """
    chain = find_chain(lessons, ctx, teacher_id, s1, s2)
    after = apply_chain(lessons, chain, s1, s2)
    teacher_ids = {ctx.teacher_of(lesson) for lesson in chain}
    days = {s1[0], s2[0]}

    before_counts = count_violations(lessons, ctx, teacher_ids, days)
    after_counts = count_violations(after, ctx, teacher_ids, days)
    worsened = [key for key, count in after_counts.items() if count > before_counts[key]]
    if worsened:
        raise SwapError(
            "the swap breaks " + "; ".join(_describe(ctx, *key) for key in sorted(worsened, key=str))
        )

    warnings = []
    for tid in sorted(teacher_ids):
        for day in sorted(days):
            old = _day_quality(lessons, ctx, tid, day)
            new = _day_quality(after, ctx, tid, day)
            for metric in WARNING_METRICS:
                if new[metric] > old[metric]:
                    warnings.append({
                        "teacher_id": tid,
                        "teacher": ctx.teacher_name(tid),
                        "day": day,
                        "metric": metric,
                        "before": old[metric],
                        "after": new[metric],
                    })
    return after, chain, warnings


def replay(
    lessons: list[Lesson], ctx: SwapContext, applied: list[tuple[int, Slot, Slot]]
) -> list[Lesson]:
    """Re-apply a sequence of swaps, rechecking each one against current data."""
    for index, (teacher_id, s1, s2) in enumerate(applied):
        try:
            lessons, _, _ = check_swap(lessons, ctx, teacher_id, s1, s2)
        except SwapError as error:
            raise SwapError(f"swap {index + 1}: {error}") from error
    return lessons


def suggest(
    lessons: list[Lesson], ctx: SwapContext, teacher_id: int, s1: Slot
) -> list[dict[str, Any]]:
    """Every admissible swap of the lesson (teacher, s1): clean ones first, then shorter chains."""
    def cell(teacher: int, slot: Slot) -> dict[str, Any] | None:
        for lesson in lessons:
            if lesson.slot == slot and ctx.teacher_of(lesson) == teacher:
                assignment = ctx.assignments[lesson.assignment_id]
                return {
                    "class_id": assignment.class_id,
                    "class": assignment.school_class.name,
                    "matter": assignment.matter.name,
                }
        return None

    candidates = []
    for s2 in ALL_SLOTS:
        try:
            _, chain, warnings = check_swap(lessons, ctx, teacher_id, s1, s2)
        except SwapError:
            continue
        teacher_ids = sorted({ctx.teacher_of(lesson) for lesson in chain})
        candidates.append({
            "s2": {"day": s2[0], "hour": s2[1]},
            "teachers": [
                {
                    "teacher_id": tid,
                    "teacher": ctx.teacher_name(tid),
                    "before_s1": cell(tid, s1),
                    "before_s2": cell(tid, s2),
                }
                for tid in teacher_ids
            ],
            "warnings": warnings,
        })
    candidates.sort(key=lambda c: (bool(c["warnings"]), len(c["teachers"])))
    return candidates
