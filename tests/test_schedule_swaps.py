"""Manual swaps on a saved timetable: chain, validation, warnings, suggestions."""

import pytest

from squola.models import (
    ClassMatterAssignment,
    FixedClassLesson,
    Matter,
    MatterRequirements,
    SchoolClass,
    Teacher,
    TeacherUnavailability,
)
from squola.scheduler import DAY_NAMES, HOUR_LABELS, SchedulingData
from squola.swaps import (
    Lesson,
    SwapContext,
    SwapError,
    check_swap,
    count_violations,
    find_chain,
    load_lessons,
    replay,
    suggest,
)

TEACHERS = {"MR": 1, "GV": 2, "RM": 3, "MG": 4}


class World:
    """Teachers by initials, classes by name, one assignment per (teacher, class, matter)."""

    def __init__(self) -> None:
        self.teachers = {
            initials: Teacher(
                id=tid, workspace_id=1, first_name=initials, last_name="X",
                schedule_preference="none", prefers_day_off=False,
            )
            for initials, tid in TEACHERS.items()
        }
        self.classes: dict[str, SchoolClass] = {}
        self.matters: dict[str, Matter] = {}
        self.assignments: dict[tuple[str, str, str], ClassMatterAssignment] = {}
        self.unavailabilities: list[TeacherUnavailability] = []
        self.fixed: list[FixedClassLesson] = []
        self.lessons: list[Lesson] = []

    def assignment(self, teacher: str, class_name: str, matter: str = "", **kw) -> ClassMatterAssignment:
        matter = matter or f"M-{teacher}"
        key = (teacher, class_name, matter)
        if key not in self.assignments:
            school_class = self.classes.setdefault(
                class_name,
                SchoolClass(id=len(self.classes) + 1, workspace_id=1,
                            year=class_name[0], section=class_name[1:]),
            )
            matter_obj = self.matters.setdefault(
                matter, Matter(id=len(self.matters) + 1, workspace_id=1, name=matter)
            )
            teacher_obj = self.teachers[teacher]
            self.assignments[key] = ClassMatterAssignment(
                id=len(self.assignments) + 1, workspace_id=1,
                class_id=school_class.id, matter_id=matter_obj.id, teacher_id=teacher_obj.id,
                hours_per_week=kw.get("hours_per_week", 3), requirements=kw.get("requirements", []),
                teacher=teacher_obj, school_class=school_class, matter=matter_obj,
            )
        return self.assignments[key]

    def lesson(self, teacher: str, class_name: str, day: int, hour: int, matter: str = "", **kw) -> Lesson:
        lesson = Lesson(self.assignment(teacher, class_name, matter, **kw).id, day, hour)
        self.lessons.append(lesson)
        return lesson

    def ctx(self) -> SwapContext:
        return SwapContext(SchedulingData(
            teachers=list(self.teachers.values()),
            classes=list(self.classes.values()),
            assignments=list(self.assignments.values()),
            unavailabilities=self.unavailabilities,
            fixed_lessons=self.fixed,
        ))

    def unavailable(self, teacher: str, day: int, hour: int) -> None:
        self.unavailabilities.append(TeacherUnavailability(
            id=len(self.unavailabilities) + 1, workspace_id=1,
            teacher_id=TEACHERS[teacher], day_of_week=day, hour_slot=hour,
        ))


def where(world: World, ctx: SwapContext, lessons: list[Lesson], day: int, hour: int) -> dict[str, str]:
    """Teacher initials -> class name in one slot."""
    initials = {tid: name for name, tid in TEACHERS.items()}
    return {
        initials[ctx.teacher_of(l)]: ctx.assignments[l.assignment_id].school_class.name
        for l in lessons
        if (l.day, l.hour) == (day, hour)
    }


def simple_world() -> World:
    """3A: MR at h1, GV at h2. MR also in 1B at h3, GV also in 2C at h4 (Monday)."""
    world = World()
    world.lesson("MR", "3A", 0, 1)
    world.lesson("GV", "3A", 0, 2)
    world.lesson("MR", "1B", 0, 3)
    world.lesson("GV", "2C", 0, 4)
    return world


def test_simple_swap_between_two_teachers():
    world = simple_world()
    ctx = world.ctx()

    after, chain, warnings = check_swap(world.lessons, ctx, TEACHERS["MR"], (0, 1), (0, 2))

    assert len(chain) == 2
    assert where(world, ctx, after, 0, 1) == {"GV": "3A"}
    assert where(world, ctx, after, 0, 2) == {"MR": "3A"}


def test_three_teacher_cycle():
    world = World()
    for teacher, first, second in [("GV", "1B", "2C"), ("RM", "3A", "1B"), ("MG", "2C", "3A")]:
        world.lesson(teacher, first, 0, 1)
        world.lesson(teacher, second, 0, 2)
    ctx = world.ctx()

    after, chain, _ = check_swap(world.lessons, ctx, TEACHERS["GV"], (0, 1), (0, 2))

    assert len(chain) == 6
    assert where(world, ctx, after, 0, 1) == {"GV": "2C", "RM": "1B", "MG": "3A"}
    assert where(world, ctx, after, 0, 2) == {"GV": "1B", "RM": "3A", "MG": "2C"}


def test_weekly_hours_are_unchanged():
    world = World()
    for teacher, first, second in [("GV", "1B", "2C"), ("RM", "3A", "1B"), ("MG", "2C", "3A")]:
        world.lesson(teacher, first, 0, 1)
        world.lesson(teacher, second, 0, 2)
    ctx = world.ctx()

    after, _, _ = check_swap(world.lessons, ctx, TEACHERS["GV"], (0, 1), (0, 2))

    count = lambda lessons: sorted(l.assignment_id for l in lessons)
    assert count(after) == count(world.lessons)


def test_class_with_a_lesson_in_one_slot_only_is_rejected():
    world = World()
    world.lesson("MR", "3A", 0, 1)
    world.lesson("MR", "1B", 0, 3)

    with pytest.raises(SwapError, match="without a lesson"):
        find_chain(world.lessons, world.ctx(), TEACHERS["MR"], (0, 1), (0, 2))


def test_fixed_lesson_in_the_chain_is_rejected():
    world = simple_world()
    gv = world.assignment("GV", "3A")
    world.fixed.append(FixedClassLesson(
        id=1, workspace_id=1, class_id=gv.class_id, assignment_id=gv.id, day_of_week=0, hour_slot=2,
    ))

    with pytest.raises(SwapError, match="fixed"):
        find_chain(world.lessons, world.ctx(), TEACHERS["MR"], (0, 1), (0, 2))


def test_teacher_with_two_matters_in_one_class_swaps_them():
    world = World()
    maths = world.lesson("MR", "3A", 0, 1, "Matematica")
    physics = world.lesson("MR", "3A", 0, 2, "Fisica")
    ctx = world.ctx()

    after, _, _ = check_swap(world.lessons, ctx, TEACHERS["MR"], (0, 1), (0, 2))

    assert Lesson(maths.assignment_id, 0, 2) in after
    assert Lesson(physics.assignment_id, 0, 1) in after


def test_swap_without_effect_is_rejected():
    world = World()
    world.lesson("MR", "3A", 0, 1)
    world.lesson("MR", "3A", 0, 2)

    with pytest.raises(SwapError, match="no effect"):
        find_chain(world.lessons, world.ctx(), TEACHERS["MR"], (0, 1), (0, 2))


def test_fourth_hour_of_one_matter_in_a_day_is_rejected():
    world = World()
    for hour in (1, 2, 3):
        world.lesson("MR", "3A", 0, hour, "Matematica")
    world.lesson("GV", "3A", 0, 5)
    world.lesson("GV", "1B", 0, 6)
    world.lesson("MR", "3A", 1, 1, "Matematica")
    world.lesson("MR", "1B", 1, 2)

    with pytest.raises(SwapError, match="daily_cap"):
        check_swap(world.lessons, world.ctx(), TEACHERS["MR"], (1, 1), (0, 5))


def test_swap_into_an_unavailable_slot_is_rejected():
    world = simple_world()
    world.unavailable("GV", 0, 1)

    with pytest.raises(SwapError, match="unavailable"):
        check_swap(world.lessons, world.ctx(), TEACHERS["MR"], (0, 1), (0, 2))


def test_swap_leaving_a_one_hour_day_is_rejected():
    world = simple_world()
    world.lesson("GV", "3A", 1, 1)
    world.lesson("GV", "2C", 1, 2)

    with pytest.raises(SwapError, match="daily_hours"):
        check_swap(world.lessons, world.ctx(), TEACHERS["MR"], (0, 1), (1, 1))


def test_flexible_day_off_cannot_be_filled():
    world = World()
    world.teachers["MR"].prefers_day_off = True
    for day in range(4):
        world.lesson("MR", "1B", day, 1)
        world.lesson("MR", "1B", day, 2)
    world.lesson("MR", "3A", 0, 3)
    world.lesson("GV", "3A", 4, 1)
    world.lesson("GV", "3A", 4, 2)

    ctx = world.ctx()
    with pytest.raises(SwapError):
        check_swap(world.lessons, ctx, TEACHERS["MR"], (0, 3), (4, 1))
    assert count_violations(world.lessons, ctx, {TEACHERS["MR"]}, set(range(5))) == {}


def test_at_least_twice_per_week_is_enforced():
    twice = {"requirements": [MatterRequirements.AT_LEAST_TWICE_PER_WEEK], "hours_per_week": 2}
    world = World()
    world.lesson("MR", "3A", 0, 1, **twice)
    world.lesson("MR", "1B", 0, 2)
    world.lesson("MR", "3A", 1, 1, **twice)
    world.lesson("MR", "1B", 1, 2)
    world.lesson("GV", "3A", 0, 3)
    world.lesson("GV", "1B", 0, 4)

    # Bringing Tuesday's hour next to Monday's leaves the matter on one day.
    with pytest.raises(SwapError, match="at_least_twice_per_week"):
        check_swap(world.lessons, world.ctx(), TEACHERS["MR"], (1, 1), (0, 3))


@pytest.mark.parametrize(
    "requirement", [MatterRequirements.ONE_LESSON_OF_TWO_HOURS_PER_WEEK]
)
def test_block_requirement_is_enforced(requirement):
    block = {"requirements": [requirement]}
    world = World()
    world.lesson("MR", "3A", 0, 1, **block)
    world.lesson("MR", "3A", 0, 2, **block)
    world.lesson("MR", "3A", 0, 5, **block)
    world.lesson("GV", "3A", 0, 3)
    world.lesson("GV", "1B", 0, 4)

    with pytest.raises(SwapError, match=requirement.value):
        check_swap(world.lessons, world.ctx(), TEACHERS["MR"], (0, 2), (0, 3))


def test_three_hour_block_requirement_is_enforced():
    block = {"requirements": [MatterRequirements.ONE_LESSON_OF_THREE_HOURS_PER_WEEK]}
    world = World()
    for hour in (1, 2, 3):
        world.lesson("MR", "3A", 0, hour, **block)
    world.lesson("GV", "3A", 0, 4)
    world.lesson("GV", "1B", 0, 5)

    with pytest.raises(SwapError, match="one_lesson_of_three_hours_per_week"):
        check_swap(world.lessons, world.ctx(), TEACHERS["MR"], (0, 3), (0, 4))


def test_existing_violation_that_is_not_worsened_does_not_reject():
    world = simple_world()
    world.unavailable("MR", 0, 3)  # MR already teaches 1B there

    after, _, _ = check_swap(world.lessons, world.ctx(), TEACHERS["MR"], (0, 1), (0, 2))

    assert after != world.lessons


def test_swap_opening_a_second_gap_hour_is_proposed_with_a_warning():
    world = World()
    world.lesson("MR", "3A", 0, 1)
    world.lesson("MR", "1B", 0, 2)
    world.lesson("GV", "2C", 0, 2)
    world.lesson("GV", "3A", 0, 4)

    _, _, warnings = check_swap(world.lessons, world.ctx(), TEACHERS["MR"], (0, 1), (0, 4))

    assert warnings == [{
        "teacher_id": TEACHERS["MR"], "teacher": "MR X", "day": 0,
        "metric": "excess_gap_hours", "before": 0, "after": 1,
    }]


def test_suggestions_list_clean_swaps_first():
    world = World()
    world.lesson("MR", "3A", 0, 1)
    world.lesson("MR", "1B", 0, 2)
    world.lesson("GV", "2C", 0, 2)
    world.lesson("GV", "3A", 0, 4)   # swapping here opens a gap for MR
    world.lesson("RM", "4D", 0, 2)
    world.lesson("RM", "3A", 0, 3)   # swapping here keeps everyone contiguous

    candidates = suggest(world.lessons, world.ctx(), TEACHERS["MR"], (0, 1))

    assert [c["s2"] for c in candidates] == [{"day": 0, "hour": 3}, {"day": 0, "hour": 4}]
    assert not candidates[0]["warnings"] and candidates[1]["warnings"]
    assert candidates[0]["teachers"] == [
        {"teacher_id": 1, "teacher": "MR X",
         "before_s1": {"class_id": 1, "class": "3A", "matter": "M-MR"}, "before_s2": None},
        {"teacher_id": 3, "teacher": "RM X",
         "before_s1": None, "before_s2": {"class_id": 1, "class": "3A", "matter": "M-RM"}},
    ]


def test_suggestions_prefer_shorter_chains():
    world = World()
    for teacher, first, second in [("GV", "1B", "2C"), ("RM", "3A", "1B"), ("MG", "2C", "3A")]:
        world.lesson(teacher, first, 0, 1)
        world.lesson(teacher, second, 0, 2)
    world.lesson("MR", "4D", 0, 2)
    world.lesson("MR", "1B", 0, 3)  # a two-teacher swap with GV at h3

    candidates = suggest(world.lessons, world.ctx(), TEACHERS["GV"], (0, 1))

    assert [(c["s2"]["hour"], len(c["teachers"]), bool(c["warnings"])) for c in candidates] == [
        (3, 2, False), (2, 3, False),
    ]


def test_empty_cell_has_no_suggestions():
    world = simple_world()

    assert suggest(world.lessons, world.ctx(), TEACHERS["MR"], (0, 2)) == []


def test_replay_rejects_an_invalid_swap_by_position():
    world = simple_world()
    applied = [(TEACHERS["MR"], (0, 1), (0, 2)), (TEACHERS["MR"], (0, 1), (0, 2))]

    with pytest.raises(SwapError, match="swap 2"):
        replay(world.lessons, world.ctx(), applied)


def saved(world: World, lessons: list[Lesson], *, with_ids: bool) -> dict:
    ctx = world.ctx()
    by_class: dict[str, list] = {}
    for lesson in lessons:
        slot = ctx.to_schedule_slot(lesson)
        entry = {"day": DAY_NAMES[slot.day], "hour": HOUR_LABELS[slot.hour - 1],
                 "teacher": slot.teacher_name, "matter": slot.matter_name}
        if with_ids:
            entry.update(slot.ids())
        by_class.setdefault(slot.class_name, []).append(entry)
    return {"by_class": by_class}


@pytest.mark.parametrize("with_ids", [True, False])
def test_saved_timetable_is_linked_to_current_assignments(with_ids: bool):
    world = simple_world()

    lessons, unlinked = load_lessons(saved(world, world.lessons, with_ids=with_ids), world.ctx())

    assert sorted(lessons, key=str) == sorted(world.lessons, key=str)
    assert unlinked == []


def test_old_timetable_with_a_renamed_teacher_is_not_linked():
    world = simple_world()
    data = saved(world, world.lessons, with_ids=False)
    world.teachers["GV"].first_name = "Guido"

    _, unlinked = load_lessons(data, world.ctx())

    assert {entry["teacher"] for entry in unlinked} == {"GV X"}
    assert len(unlinked) == 2


def test_timetable_with_a_deleted_assignment_is_not_linked():
    world = simple_world()
    data = saved(world, world.lessons, with_ids=True)
    del world.assignments[("GV", "2C", "M-GV")]

    _, unlinked = load_lessons(data, world.ctx())

    assert [(entry["class"], entry["teacher"]) for entry in unlinked] == [("2C", "GV X")]


def generator_world() -> World:
    """Three teachers and two classes exercising every hard rule the validator mirrors."""
    world = World()
    world.teachers["RM"].prefers_day_off = True
    for day_hour in range(1, 7):
        world.unavailable("GV", 0, day_hour)
    world.unavailable("MR", 2, 1)
    twice = [MatterRequirements.AT_LEAST_TWICE_PER_WEEK, MatterRequirements.ONE_LESSON_OF_TWO_HOURS_PER_WEEK]
    world.assignment("MR", "1A", "Matematica", hours_per_week=5, requirements=twice)
    world.assignment("MR", "1B", "Matematica", hours_per_week=5)
    world.assignment("GV", "1A", "Italiano", hours_per_week=6,
                     requirements=[MatterRequirements.ONE_LESSON_OF_THREE_HOURS_PER_WEEK])
    world.assignment("GV", "1B", "Italiano", hours_per_week=6)
    world.assignment("RM", "1A", "Inglese", hours_per_week=4,
                     requirements=[MatterRequirements.MAX_TWO_HOURS_PER_DAY])
    world.assignment("RM", "1B", "Inglese", hours_per_week=4)
    return world


def test_generated_timetables_have_no_violations():
    from squola.scheduler import ScheduleGenerator

    world = generator_world()
    ctx = world.ctx()
    generator = ScheduleGenerator(ctx.data)
    generator.build_model(with_objective=False)
    schedule = generator.solve(time_limit_seconds=10)
    assert schedule.status in {"OPTIMAL", "FEASIBLE"}

    lessons = [Lesson(s.assignment_id, s.day, s.hour) for s in schedule.slots]
    assert count_violations(lessons, ctx, set(ctx.teachers), set(range(5))) == {}
    # Every suggestion keeps the timetable valid too.
    for lesson in lessons[:10]:
        teacher_id = ctx.teacher_of(lesson)
        for candidate in suggest(lessons, ctx, teacher_id, lesson.slot):
            s2 = (candidate["s2"]["day"], candidate["s2"]["hour"])
            after, _, _ = check_swap(lessons, ctx, teacher_id, lesson.slot, s2)
            assert count_violations(after, ctx, set(ctx.teachers), set(range(5))) == {}
