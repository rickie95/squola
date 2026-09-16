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


def test_completing_full_day_unavailability_clears_flexible_day_off(client: TestClient):
    client.post(
        "/api/auth/register",
        json={"username": "alice", "password": "alice-password12"},
    )
    teacher = client.post(
        "/api/teachers",
        json={"first_name": "Alice", "last_name": "Rossi", "prefers_day_off": True},
    ).json()

    for hour in range(1, 6):
        response = client.post(
            f"/api/teachers/{teacher['id']}/unavailabilities",
            json={"day_of_week": 0, "hour_slot": hour},
        )
        assert response.status_code == 201
        assert client.get(f"/api/teachers/{teacher['id']}").json()["prefers_day_off"] is True

    completed = client.post(
        f"/api/teachers/{teacher['id']}/unavailabilities",
        json={"day_of_week": 0, "hour_slot": 6},
    )

    assert completed.status_code == 201
    assert client.get(f"/api/teachers/{teacher['id']}").json()["prefers_day_off"] is False


def test_flexible_day_off_is_rejected_when_full_day_is_unavailable(client: TestClient):
    client.post(
        "/api/auth/register",
        json={"username": "alice", "password": "alice-password12"},
    )
    teacher = client.post(
        "/api/teachers",
        json={"first_name": "Alice", "last_name": "Rossi"},
    ).json()
    for hour in range(1, 7):
        response = client.post(
            f"/api/teachers/{teacher['id']}/unavailabilities",
            json={"day_of_week": 0, "hour_slot": hour},
        )
        assert response.status_code == 201

    rejected = client.put(
        f"/api/teachers/{teacher['id']}",
        json={"prefers_day_off": True},
    )

    assert rejected.status_code == 409
    assert "fully unavailable weekday" in rejected.json()["detail"]


def test_partial_unavailability_does_not_prevent_flexible_day_off(client: TestClient):
    client.post(
        "/api/auth/register",
        json={"username": "alice", "password": "alice-password12"},
    )
    teacher = client.post(
        "/api/teachers",
        json={"first_name": "Alice", "last_name": "Rossi"},
    ).json()
    response = client.post(
        f"/api/teachers/{teacher['id']}/unavailabilities",
        json={"day_of_week": 0, "hour_slot": 1},
    )
    assert response.status_code == 201

    enabled = client.put(
        f"/api/teachers/{teacher['id']}",
        json={"prefers_day_off": True},
    )

    assert enabled.status_code == 200
    assert enabled.json()["prefers_day_off"] is True


def test_preview_and_generation_explain_infeasible_flexible_day_load(client: TestClient):
    client.post(
        "/api/auth/register",
        json={"username": "alice", "password": "alice-password12"},
    )
    matter = client.post(
        "/api/matters", json={"name": "Italiano", "default_requirements": []}
    ).json()
    teacher = client.post(
        "/api/teachers",
        json={"first_name": "Alice", "last_name": "Rossi", "prefers_day_off": True},
    ).json()
    school_class = client.post("/api/classes", json={"year": "1", "section": "A"}).json()
    assignment = client.post(
        f"/api/classes/{school_class['id']}/assignments",
        json={
            "matter_id": matter["id"],
            "teacher_id": teacher["id"],
            "hours_per_week": 21,
            "requirements": [],
        },
    )
    assert assignment.status_code == 201

    preview = client.get("/api/scheduling/preview")
    generated = client.post("/api/scheduling/generate", json={"time_limit_seconds": 3})

    assert any("flexible day off" in issue for issue in preview.json()["issues"])
    assert generated.status_code == 422
    assert "flexible day off" in generated.json()["detail"]


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


def test_flexible_day_off_is_hard_and_uses_four_workdays_when_possible():
    baseline_data = make_data(
        hours_per_assignment=10,
        assignments_count=1,
        prefers_day_off=False,
        preference=SchedulePreference.EARLY,
    )
    assert len(scheduled_days(baseline_data)) == 5

    flexible_day_off_data = make_data(
        hours_per_assignment=10,
        assignments_count=1,
        prefers_day_off=True,
        preference=SchedulePreference.EARLY,
    )
    assert len(scheduled_days(flexible_day_off_data)) == 4


def test_flexible_day_off_maximizes_workdays_for_low_load():
    data = make_data(
        hours_per_assignment=6,
        assignments_count=1,
        prefers_day_off=True,
    )
    assert len(scheduled_days(data)) == 3


def test_flexible_day_off_is_infeasible_when_load_requires_five_days():
    data = make_data(
        hours_per_assignment=21,
        assignments_count=1,
        prefers_day_off=True,
    )
    schedule = ScheduleGenerator(data)
    schedule.build_model()

    assert schedule.solve().status == "INFEASIBLE"


def test_full_day_unavailability_overrides_flexible_day_off():
    blocked = [
        TeacherUnavailability(
            id=hour,
            workspace_id=1,
            teacher_id=1,
            day_of_week=0,
            hour_slot=hour,
        )
        for hour in range(1, 7)
    ]
    data = make_data(
        hours_per_assignment=8,
        assignments_count=1,
        prefers_day_off=True,
        unavailabilities=blocked,
    )
    schedule = ScheduleGenerator(data)
    schedule.build_model()
    result = schedule.solve()

    assert result.status == "OPTIMAL"
    assert all(slot.day != 0 for slot in result.slots)
    assert {slot.day for slot in result.slots} == {1, 2, 3, 4}
