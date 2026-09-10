import pytest

from squola.models import (
    ClassMatterAssignment,
    FixedClassLesson,
    Matter,
    SchoolClass,
    Teacher,
    TeacherUnavailability,
)
from squola.scheduler import ScheduleGenerator, SchedulingData


def make_data(
    assignment_hours: list[int],
    *,
    unavailable_days: set[int] | None = None,
    fixed_lessons: list[FixedClassLesson] | None = None,
) -> SchedulingData:
    teacher = Teacher(id=1, workspace_id=1, first_name="Alice", last_name="Rossi")
    assignments = []
    classes = []

    for index, hours_per_week in enumerate(assignment_hours, start=1):
        school_class = SchoolClass(
            id=index,
            workspace_id=1,
            year="I",
            section=chr(ord("A") + index - 1),
        )
        matter = Matter(id=index, workspace_id=1, name=f"Matter {index}")
        assignments.append(
            ClassMatterAssignment(
                id=index,
                workspace_id=1,
                class_id=school_class.id,
                matter_id=matter.id,
                teacher_id=teacher.id,
                hours_per_week=hours_per_week,
                requirements=[],
                teacher=teacher,
                school_class=school_class,
                matter=matter,
            )
        )
        classes.append(school_class)

    unavailabilities = [
        TeacherUnavailability(
            id=day * 10 + hour,
            workspace_id=1,
            teacher_id=teacher.id,
            day_of_week=day,
            hour_slot=hour,
        )
        for day in unavailable_days or set()
        for hour in range(1, 7)
    ]

    return SchedulingData(
        teachers=[teacher],
        classes=classes,
        assignments=assignments,
        unavailabilities=unavailabilities,
        fixed_lessons=fixed_lessons or [],
    )


def solve(data: SchedulingData):
    generator = ScheduleGenerator(data)
    generator.build_model()
    return generator.solve()


@pytest.mark.parametrize("hours_per_week", [2, 3, 4, 5])
def test_legal_daily_workloads_are_feasible(hours_per_week: int):
    schedule = solve(make_data([hours_per_week], unavailable_days={1, 2, 3, 4}))

    assert schedule.status == "OPTIMAL"
    assert len(schedule.slots) == hours_per_week
    assert {slot.day for slot in schedule.slots} == {0}


def test_zero_hour_days_are_legal():
    schedule = solve(make_data([2], unavailable_days={1, 2, 3, 4}))

    assert schedule.status == "OPTIMAL"
    assert {slot.day for slot in schedule.slots} == {0}


@pytest.mark.parametrize(
    ("hours_per_week", "unavailable_days"),
    [(1, set()), (6, {1, 2, 3, 4})],
)
def test_illegal_daily_workloads_are_infeasible(
    hours_per_week: int, unavailable_days: set[int]
):
    schedule = solve(make_data([hours_per_week], unavailable_days=unavailable_days))

    assert schedule.status == "INFEASIBLE"


def test_daily_workload_combines_assignments_for_the_same_teacher():
    schedule = solve(make_data([1, 1], unavailable_days={1, 2, 3, 4}))

    assert schedule.status == "OPTIMAL"
    assert {slot.day for slot in schedule.slots} == {0}
    assert {slot.assignment_id for slot in schedule.slots} == {1, 2}


def test_fixed_single_lesson_can_be_paired_to_form_a_legal_workday():
    data = make_data([1, 1])
    fixed_lesson = FixedClassLesson(
        id=1,
        workspace_id=1,
        class_id=1,
        assignment_id=1,
        day_of_week=0,
        hour_slot=1,
        assignment=data.assignments[0],
    )
    data.fixed_lessons = [fixed_lesson]

    schedule = solve(data)

    assert schedule.status == "OPTIMAL"
    assert {(slot.day, slot.assignment_id) for slot in schedule.slots} == {(0, 1), (0, 2)}


def test_unpairable_fixed_single_lesson_is_infeasible():
    data = make_data([1])
    fixed_lesson = FixedClassLesson(
        id=1,
        workspace_id=1,
        class_id=1,
        assignment_id=1,
        day_of_week=0,
        hour_slot=1,
        assignment=data.assignments[0],
    )
    data.fixed_lessons = [fixed_lesson]

    assert solve(data).status == "INFEASIBLE"
