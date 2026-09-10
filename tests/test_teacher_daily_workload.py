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
from squola.scheduler import (
    ScheduleGenerator,
    SchedulingData,
    find_teachers_with_unsatisfiable_daily_workload,
)


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


def make_assignment_with_requirement(
    *, assignment_id: int, hours_per_week: int, requirements: list[MatterRequirements]
) -> ClassMatterAssignment:
    teacher = Teacher(id=1, workspace_id=1, first_name="Alice", last_name="Rossi")
    school_class = SchoolClass(
        id=assignment_id, workspace_id=1, year="I", section=chr(ord("A") + assignment_id - 1)
    )
    matter = Matter(id=assignment_id, workspace_id=1, name=f"Matter {assignment_id}")
    return ClassMatterAssignment(
        id=assignment_id,
        workspace_id=1,
        class_id=school_class.id,
        matter_id=matter.id,
        teacher_id=teacher.id,
        hours_per_week=hours_per_week,
        requirements=requirements,
        teacher=teacher,
        school_class=school_class,
        matter=matter,
    )


def test_lone_low_hour_at_least_twice_assignment_is_flagged_unsatisfiable():
    """A matter requiring 'at least twice per week' with only 2 hours/week forces
    a 1+1 split across days. If that is a teacher's only assignment, there is no
    other lesson to pad either day to the legal 2-hour minimum."""
    assignment = make_assignment_with_requirement(
        assignment_id=1,
        hours_per_week=2,
        requirements=[MatterRequirements.AT_LEAST_TWICE_PER_WEEK],
    )
    data = SchedulingData(
        teachers=[assignment.teacher],
        classes=[assignment.school_class],
        assignments=[assignment],
    )

    unsatisfiable = find_teachers_with_unsatisfiable_daily_workload(data)

    assert [t.id for t in unsatisfiable] == [assignment.teacher.id]
    # The full joint model must also be infeasible - the isolated check must
    # never report a false positive against the real solve.
    assert solve(data).status == "INFEASIBLE"


def test_padded_low_hour_at_least_twice_assignments_are_not_flagged():
    """Multiple 'at least twice per week' 2-hour assignments for the same teacher
    can interleave so each day pairs two different assignments' hours, forming a
    legal daily workload - this must not be flagged as unsatisfiable."""
    teacher = Teacher(id=1, workspace_id=1, first_name="Alice", last_name="Rossi")
    assignments = []
    classes = []
    for index in range(1, 4):
        school_class = SchoolClass(
            id=index, workspace_id=1, year="I", section=chr(ord("A") + index - 1)
        )
        matter = Matter(id=index, workspace_id=1, name=f"Matter {index}")
        assignments.append(
            ClassMatterAssignment(
                id=index,
                workspace_id=1,
                class_id=school_class.id,
                matter_id=matter.id,
                teacher_id=teacher.id,
                hours_per_week=2,
                requirements=[MatterRequirements.AT_LEAST_TWICE_PER_WEEK],
                teacher=teacher,
                school_class=school_class,
                matter=matter,
            )
        )
        classes.append(school_class)

    data = SchedulingData(teachers=[teacher], classes=classes, assignments=assignments)

    assert find_teachers_with_unsatisfiable_daily_workload(data) == []
    assert solve(data).status in ("OPTIMAL", "FEASIBLE")


def test_teacher_without_assignments_is_not_flagged():
    teacher = Teacher(id=1, workspace_id=1, first_name="Alice", last_name="Rossi")
    data = SchedulingData(teachers=[teacher], classes=[], assignments=[])

    assert find_teachers_with_unsatisfiable_daily_workload(data) == []


def _create_unsatisfiable_assignment(client) -> None:
    """Create a teacher whose sole assignment can never satisfy the legal daily
    workload: 2 hours/week split across 2 days by 'at least twice per week',
    with no other lesson to pad either day."""
    matter = client.post(
        "/api/matters",
        json={"name": "Musica", "default_requirements": []},
    )
    assert matter.status_code == 201
    teacher = client.post(
        "/api/teachers",
        json={"first_name": "Spezz", "last_name": "One"},
    )
    assert teacher.status_code == 201
    school_class = client.post("/api/classes", json={"year": "I", "section": "A"})
    assert school_class.status_code == 201
    assignment = client.post(
        f"/api/classes/{school_class.json()['id']}/assignments",
        json={
            "matter_id": matter.json()["id"],
            "teacher_id": teacher.json()["id"],
            "hours_per_week": 2,
            "requirements": ["at_least_twice_per_week"],
        },
    )
    assert assignment.status_code == 201


def test_preview_reports_teachers_with_unsatisfiable_daily_workload(client):
    client.post(
        "/api/auth/register",
        json={"username": "alice", "password": "alice-password12"},
    )
    _create_unsatisfiable_assignment(client)

    preview = client.get("/api/scheduling/preview")

    assert preview.status_code == 200
    issues = preview.json()["issues"]
    assert any("Spezz One" in issue for issue in issues)


def test_generate_reports_unsatisfiable_teacher_in_error_detail(client):
    client.post(
        "/api/auth/register",
        json={"username": "alice", "password": "alice-password12"},
    )
    _create_unsatisfiable_assignment(client)

    generated = client.post("/api/scheduling/generate", json={"time_limit_seconds": 3})

    assert generated.status_code == 422
    assert "Spezz One" in generated.json()["detail"]


