from fastapi.testclient import TestClient

from squola.models import (
    ClassMatterAssignment,
    Matter,
    SchedulePreference,
    SchoolClass,
    Teacher,
    TeacherUnavailability,
)
from squola.scheduler import ScheduleGenerator, SchedulingData


def test_teacher_day_off_preference_defaults_and_can_be_updated(client: TestClient):
    client.post(
        "/api/auth/register",
        json={"username": "alice", "password": "alice-password12"},
    )
    created = client.post(
        "/api/teachers",
        json={"first_name": "Alice", "last_name": "Rossi"},
    )
    assert created.status_code == 201
    teacher = created.json()
    assert teacher["prefers_day_off"] is False

    updated = client.put(
        f"/api/teachers/{teacher['id']}",
        json={"prefers_day_off": True},
    )
    assert updated.status_code == 200
    assert updated.json()["prefers_day_off"] is True

    preview = client.get("/api/scheduling/preview")
    assert preview.status_code == 200
    assert preview.json()["summary"]["flexible_day_off_requests_count"] == 1
    assert preview.json()["teachers"] == [
        {
            "id": teacher["id"],
            "name": "Alice Rossi",
            "hours_assigned": 0,
            "unavailabilities_count": 0,
            "preference": "none",
            "prefers_day_off": True,
        }
    ]

    disabled = client.put(
        f"/api/teachers/{teacher['id']}",
        json={"prefers_day_off": False},
    )
    assert disabled.status_code == 200
    assert disabled.json()["prefers_day_off"] is False


def make_data(
    *,
    hours_per_assignment: int,
    assignments_count: int,
    prefers_day_off: bool,
    preference: SchedulePreference = SchedulePreference.NONE,
    unavailabilities: list[TeacherUnavailability] | None = None,
) -> SchedulingData:
    teacher = Teacher(
        id=1,
        workspace_id=1,
        first_name="Alice",
        last_name="Rossi",
        schedule_preference=preference.value,
        prefers_day_off=prefers_day_off,
    )
    assignments = []
    classes = []
    for index in range(assignments_count):
        school_class = SchoolClass(
            id=index + 1, workspace_id=1, year="I", section=chr(ord("A") + index)
        )
        matter = Matter(id=index + 1, workspace_id=1, name=f"Matter {index + 1}")
        assignments.append(
            ClassMatterAssignment(
                id=index + 1,
                workspace_id=1,
                class_id=school_class.id,
                matter_id=matter.id,
                teacher_id=teacher.id,
                hours_per_week=hours_per_assignment,
                requirements=[],
                teacher=teacher,
                school_class=school_class,
                matter=matter,
            )
        )
        classes.append(school_class)

    return SchedulingData(
        teachers=[teacher],
        classes=classes,
        assignments=assignments,
        unavailabilities=unavailabilities or [],
    )


def scheduled_days(data: SchedulingData) -> set[int]:
    schedule = ScheduleGenerator(data)
    schedule.build_model()
    result = schedule.solve()
    assert result.status == "OPTIMAL"
    return {slot.day for slot in result.slots}


def test_flexible_day_off_outranks_early_preference():
    baseline_data = make_data(
        hours_per_assignment=5,
        assignments_count=4,
        prefers_day_off=False,
        preference=SchedulePreference.EARLY,
    )
    assert len(scheduled_days(baseline_data)) == 5

    flexible_day_off_data = make_data(
        hours_per_assignment=5,
        assignments_count=4,
        prefers_day_off=True,
        preference=SchedulePreference.EARLY,
    )
    assert len(scheduled_days(flexible_day_off_data)) <= 4


def test_flexible_day_off_is_relaxed_when_five_days_are_required():
    unavailable = [
        TeacherUnavailability(
            id=day * 10 + hour,
            workspace_id=1,
            teacher_id=1,
            day_of_week=day,
            hour_slot=hour,
        )
        for day in range(5)
        for hour in range(3, 7)
    ]
    data = make_data(
        hours_per_assignment=10,
        assignments_count=1,
        prefers_day_off=True,
        unavailabilities=unavailable,
    )
    assert scheduled_days(data) == {0, 1, 2, 3, 4}


def test_fixed_unavailability_remains_hard_with_flexible_day_off():
    blocked = TeacherUnavailability(
        id=1, workspace_id=1, teacher_id=1, day_of_week=0, hour_slot=1
    )
    data = make_data(
        hours_per_assignment=2,
        assignments_count=1,
        prefers_day_off=True,
        unavailabilities=[blocked],
    )
    schedule = ScheduleGenerator(data)
    schedule.build_model()
    result = schedule.solve()

    assert result.status == "OPTIMAL"
    assert all(not (slot.day == 0 and slot.hour == 1) for slot in result.slots)
    assert len({slot.day for slot in result.slots}) <= 4
