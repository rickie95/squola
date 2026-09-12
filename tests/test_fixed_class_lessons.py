from fastapi.testclient import TestClient

from squola.models import (
    ClassMatterAssignment,
    FixedClassLesson,
    Matter,
    MatterRequirements,
    SchoolClass,
    Teacher,
)
from squola.scheduler import ScheduleGenerator, SchedulingData


def create_assignment(
    client: TestClient,
    *,
    class_year: str,
    class_section: str,
    matter_name: str,
    teacher_name: str = "Mario",
    teacher_surname: str = "Rossi",
    hours_per_week: int = 2,
) -> tuple[int, int, int]:
    matter = client.post(
        "/api/matters",
        json={"name": matter_name, "default_requirements": []},
    )
    assert matter.status_code == 201
    teacher = client.post(
        "/api/teachers",
        json={"first_name": teacher_name, "last_name": teacher_surname},
    )
    assert teacher.status_code == 201
    school_class = client.post(
        "/api/classes",
        json={"year": class_year, "section": class_section},
    )
    assert school_class.status_code == 201
    assignment = client.post(
        f"/api/classes/{school_class.json()['id']}/assignments",
        json={
            "matter_id": matter.json()["id"],
            "teacher_id": teacher.json()["id"],
            "hours_per_week": hours_per_week,
            "requirements": [],
        },
    )
    assert assignment.status_code == 201
    return school_class.json()["id"], teacher.json()["id"], assignment.json()["id"]


def register(client: TestClient, username: str = "alice") -> None:
    response = client.post(
        "/api/auth/register",
        json={"username": username, "password": f"{username}-password12"},
    )
    assert response.status_code == 201


def test_fixed_lesson_can_be_created_updated_and_removed(client: TestClient):
    register(client)
    class_id, _, assignment_id = create_assignment(
        client, class_year="3", class_section="A", matter_name="Italiano"
    )

    created = client.post(
        f"/api/classes/{class_id}/fixed-lessons",
        json={"assignment_id": assignment_id, "day_of_week": 1, "hour_slot": 1},
    )
    assert created.status_code == 201
    fixed_lesson = created.json()
    assert fixed_lesson["assignment"]["matter"]["name"] == "Italiano"

    updated = client.put(
        f"/api/classes/{class_id}/fixed-lessons/{fixed_lesson['id']}",
        json={"assignment_id": assignment_id},
    )
    assert updated.status_code == 200

    details = client.get(f"/api/classes/{class_id}")
    assert details.status_code == 200
    assert details.json()["fixed_lessons"] == [fixed_lesson]

    deleted = client.delete(f"/api/classes/{class_id}/fixed-lessons/{fixed_lesson['id']}")
    assert deleted.status_code == 204
    assert client.get(f"/api/classes/{class_id}").json()["fixed_lessons"] == []


def test_fixed_lesson_rejects_teacher_conflicts_and_excess_hours(client: TestClient):
    register(client)
    class_id, teacher_id, assignment_id = create_assignment(
        client, class_year="I", class_section="A", matter_name="Italiano", hours_per_week=1
    )
    other_matter = client.post(
        "/api/matters", json={"name": "Storia", "default_requirements": []}
    ).json()
    other_class = client.post("/api/classes", json={"year": "I", "section": "B"}).json()
    other_assignment = client.post(
        f"/api/classes/{other_class['id']}/assignments",
        json={
            "matter_id": other_matter["id"],
            "teacher_id": teacher_id,
            "hours_per_week": 2,
            "requirements": [],
        },
    ).json()

    created = client.post(
        f"/api/classes/{class_id}/fixed-lessons",
        json={"assignment_id": assignment_id, "day_of_week": 0, "hour_slot": 1},
    )
    assert created.status_code == 201

    teacher_conflict = client.post(
        f"/api/classes/{other_class['id']}/fixed-lessons",
        json={
            "assignment_id": other_assignment["id"],
            "day_of_week": 0,
            "hour_slot": 1,
        },
    )
    assert teacher_conflict.status_code == 400
    assert "already has a fixed lesson" in teacher_conflict.json()["detail"]

    excess_hours = client.post(
        f"/api/classes/{class_id}/fixed-lessons",
        json={"assignment_id": assignment_id, "day_of_week": 0, "hour_slot": 2},
    )
    assert excess_hours.status_code == 400
    assert client.get(f"/api/classes/{class_id}").json()["fixed_lessons"] == [created.json()]


def test_fixed_lesson_rejects_teacher_unavailability_in_either_order(client: TestClient):
    register(client)
    class_id, teacher_id, assignment_id = create_assignment(
        client, class_year="2", class_section="A", matter_name="Matematica"
    )

    unavailable = client.post(
        f"/api/teachers/{teacher_id}/unavailabilities",
        json={"day_of_week": 2, "hour_slot": 3},
    )
    assert unavailable.status_code == 201
    rejected = client.post(
        f"/api/classes/{class_id}/fixed-lessons",
        json={"assignment_id": assignment_id, "day_of_week": 2, "hour_slot": 3},
    )
    assert rejected.status_code == 400
    assert "unavailable" in rejected.json()["detail"]

    created = client.post(
        f"/api/classes/{class_id}/fixed-lessons",
        json={"assignment_id": assignment_id, "day_of_week": 2, "hour_slot": 4},
    )
    assert created.status_code == 201
    reverse_rejected = client.post(
        f"/api/teachers/{teacher_id}/unavailabilities",
        json={"day_of_week": 2, "hour_slot": 4},
    )
    assert reverse_rejected.status_code == 400
    assert "fixed lesson" in reverse_rejected.json()["detail"]


def test_assignment_lifecycle_preserves_fixed_lesson_integrity(client: TestClient):
    register(client)
    class_id, _, assignment_id = create_assignment(
        client, class_year="IV", class_section="A", matter_name="Scienze", hours_per_week=2
    )
    for hour_slot in (1, 2):
        response = client.post(
            f"/api/classes/{class_id}/fixed-lessons",
            json={"assignment_id": assignment_id, "day_of_week": 1, "hour_slot": hour_slot},
        )
        assert response.status_code == 201

    reduced = client.put(
        f"/api/classes/{class_id}/assignments/{assignment_id}",
        json={"hours_per_week": 1},
    )
    assert reduced.status_code == 400

    cloned = client.post(
        f"/api/classes/{class_id}/clone",
        json={"year": "IV", "section": "B"},
    )
    assert cloned.status_code == 201
    assert client.get(f"/api/classes/{cloned.json()['id']}").json()["fixed_lessons"] == []

    deleted = client.delete(f"/api/classes/{class_id}/assignments/{assignment_id}")
    assert deleted.status_code == 204
    assert client.get(f"/api/classes/{class_id}").json()["fixed_lessons"] == []


def test_fixed_lessons_are_isolated_by_workspace(client: TestClient):
    register(client, "alice")
    class_id, _, assignment_id = create_assignment(
        client, class_year="V", class_section="A", matter_name="Fisica"
    )
    client.post("/api/auth/logout")
    register(client, "bob")

    response = client.post(
        f"/api/classes/{class_id}/fixed-lessons",
        json={"assignment_id": assignment_id, "day_of_week": 0, "hour_slot": 1},
    )
    assert response.status_code == 404


def test_solver_keeps_fixed_lessons_in_their_configured_slots():
    teacher = Teacher(id=1, workspace_id=1, first_name="Mario", last_name="Rossi")
    school_class = SchoolClass(id=1, workspace_id=1, year="3", section="A")
    matter = Matter(id=1, workspace_id=1, name="Italiano")
    assignment = ClassMatterAssignment(
        id=1,
        workspace_id=1,
        class_id=school_class.id,
        matter_id=matter.id,
        teacher_id=teacher.id,
        hours_per_week=2,
        requirements=[],
        teacher=teacher,
        school_class=school_class,
        matter=matter,
    )
    fixed_lessons = [
        FixedClassLesson(
            id=hour_slot,
            workspace_id=1,
            class_id=school_class.id,
            assignment_id=assignment.id,
            day_of_week=1,
            hour_slot=hour_slot,
            assignment=assignment,
        )
        for hour_slot in (1, 2)
    ]
    data = SchedulingData(
        teachers=[teacher],
        classes=[school_class],
        assignments=[assignment],
        fixed_lessons=fixed_lessons,
    )

    generator = ScheduleGenerator(data)
    generator.build_model()
    schedule = generator.solve()

    assert schedule.status == "OPTIMAL"
    assert {(slot.day, slot.hour) for slot in schedule.slots} == {(1, 1), (1, 2)}


def test_generation_loads_and_preserves_fixed_lessons(client: TestClient):
    register(client)
    class_id, _, assignment_id = create_assignment(
        client, class_year="3", class_section="A", matter_name="Italiano"
    )
    for hour_slot in (1, 2):
        response = client.post(
            f"/api/classes/{class_id}/fixed-lessons",
            json={"assignment_id": assignment_id, "day_of_week": 1, "hour_slot": hour_slot},
        )
        assert response.status_code == 201

    generated = client.post("/api/scheduling/generate", json={"time_limit_seconds": 3})

    assert generated.status_code == 200
    lessons = generated.json()["schedule"]["by_class"]["3A"]
    assert {(lesson["day"], lesson["hour"], lesson["matter"]) for lesson in lessons} == {
        ("Tuesday", "08:00-09:00", "Italiano"),
        ("Tuesday", "09:00-10:00", "Italiano"),
    }


def test_solver_reports_infeasible_when_fixed_lessons_break_other_constraints():
    teacher = Teacher(id=1, workspace_id=1, first_name="Mario", last_name="Rossi")
    school_class = SchoolClass(id=1, workspace_id=1, year="3", section="A")
    matter = Matter(id=1, workspace_id=1, name="Italiano")
    assignment = ClassMatterAssignment(
        id=1,
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
    data = SchedulingData(
        teachers=[teacher],
        classes=[school_class],
        assignments=[assignment],
        fixed_lessons=[
            FixedClassLesson(
                id=hour_slot,
                workspace_id=1,
                class_id=school_class.id,
                assignment_id=assignment.id,
                day_of_week=1,
                hour_slot=hour_slot,
                assignment=assignment,
            )
            for hour_slot in (1, 2)
        ],
    )

    generator = ScheduleGenerator(data)
    generator.build_model()
    schedule = generator.solve()

    assert schedule.status == "INFEASIBLE"
