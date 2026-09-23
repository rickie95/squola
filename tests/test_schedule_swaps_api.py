"""Swap endpoints on saved schedules, plus the ids carried by saved timetables."""

import json

from fastapi.testclient import TestClient

from squola import database
from squola.models import SavedSchedule, Workspace
from squola.scheduler import DAY_NAMES, HOUR_LABELS

# simple_world of test_schedule_swaps: 3A has MR at h1 and GV at h2 on Monday.
LESSONS = [("MR", "3A", 1), ("GV", "3A", 2), ("MR", "1B", 3), ("GV", "2C", 4)]


def register(client: TestClient, username: str = "alice") -> None:
    response = client.post(
        "/api/auth/register", json={"username": username, "password": f"{username}-password12"}
    )
    assert response.status_code == 201


def seed_schedule(client: TestClient, *, with_ids: bool = True) -> tuple[int, dict[str, int]]:
    """Create the simple world through the API and store it as a saved schedule."""
    teachers = {
        initials: client.post(
            "/api/teachers", json={"first_name": initials, "last_name": "X"}
        ).json()["id"]
        for initials in ("MR", "GV")
    }
    matters = {
        initials: client.post(
            "/api/matters", json={"name": f"M-{initials}", "default_requirements": []}
        ).json()["id"]
        for initials in teachers
    }
    classes = {
        name: client.post(
            "/api/classes", json={"year": name[0], "section": name[1]}
        ).json()["id"]
        for name in ("3A", "1B", "2C")
    }
    by_class: dict[str, list] = {}
    assignments: dict[tuple[str, str], int] = {}
    for initials, class_name, hour in LESSONS:
        key = (initials, class_name)
        if key not in assignments:
            assignments[key] = client.post(
                f"/api/classes/{classes[class_name]}/assignments",
                json={
                    "matter_id": matters[initials], "teacher_id": teachers[initials],
                    "hours_per_week": 2, "requirements": [],
                },
            ).json()["id"]
        entry = {
            "day": DAY_NAMES[0], "hour": HOUR_LABELS[hour - 1],
            "teacher": f"{initials} X", "matter": f"M-{initials}",
        }
        if with_ids:
            entry.update(
                teacher_id=teachers[initials], class_id=classes[class_name],
                matter_id=matters[initials], assignment_id=assignments[key],
            )
        by_class.setdefault(class_name, []).append(entry)

    with database.SessionLocal() as db:
        workspace_id = db.query(Workspace).order_by(Workspace.id.desc()).first().id
        saved = SavedSchedule(
            workspace_id=workspace_id, name="Origine", status="OPTIMAL",
            solve_time_seconds=1.0, total_slots=len(LESSONS),
            schedule_data=json.dumps({"by_class": by_class, "by_teacher": {}, "by_day": {}}),
        )
        db.add(saved)
        db.commit()
        return saved.id, teachers


SWAP = lambda teachers: {
    "teacher_id": teachers["MR"], "s1": {"day": 0, "hour": 1}, "s2": {"day": 0, "hour": 2},
}


def test_generated_schedule_saves_ids(client: TestClient):
    register(client)
    matter_id = client.post(
        "/api/matters", json={"name": "Matematica", "default_requirements": []}
    ).json()["id"]
    teacher_id = client.post(
        "/api/teachers", json={"first_name": "Alice", "last_name": "Rossi"}
    ).json()["id"]
    class_id = client.post("/api/classes", json={"year": "1", "section": "A"}).json()["id"]
    assignment_id = client.post(
        f"/api/classes/{class_id}/assignments",
        json={"matter_id": matter_id, "teacher_id": teacher_id, "hours_per_week": 10, "requirements": []},
    ).json()["id"]
    assert client.post("/api/scheduling/generate", json={"time_limit_seconds": 3}).status_code == 200

    schedule_id = client.get("/api/scheduling/schedules").json()[0]["id"]
    data = client.get(f"/api/scheduling/schedules/{schedule_id}").json()["schedule_data"]

    ids = {"teacher_id": teacher_id, "class_id": class_id, "matter_id": matter_id, "assignment_id": assignment_id}
    for grouping in ("by_class", "by_teacher", "by_day"):
        entries = [entry for group in data[grouping].values() for entry in group]
        assert entries and all(ids.items() <= entry.items() for entry in entries)


def test_suggest_returns_the_admissible_swaps(client: TestClient):
    register(client)
    schedule_id, teachers = seed_schedule(client)

    response = client.post(
        f"/api/scheduling/schedules/{schedule_id}/swaps/suggest",
        json={"applied": [], "teacher_id": teachers["MR"], "slot": {"day": 0, "hour": 1}},
    )

    assert response.status_code == 200
    assert [c["s2"] for c in response.json()] == [{"day": 0, "hour": 2}]


def test_draft_reflects_the_applied_swaps(client: TestClient):
    register(client)
    schedule_id, teachers = seed_schedule(client)

    response = client.post(
        f"/api/scheduling/schedules/{schedule_id}/swaps/draft", json={"applied": [SWAP(teachers)]}
    )

    assert response.status_code == 200
    in_3a = {(l["teacher"], l["hour"]) for l in response.json()["lessons"] if l["class"] == "3A"}
    assert in_3a == {("GV X", 1), ("MR X", 2)}


def test_old_schedule_is_linked_by_name(client: TestClient):
    register(client)
    schedule_id, teachers = seed_schedule(client, with_ids=False)

    response = client.post(
        f"/api/scheduling/schedules/{schedule_id}/swaps/suggest",
        json={"teacher_id": teachers["MR"], "slot": {"day": 0, "hour": 1}},
    )

    assert response.status_code == 200 and len(response.json()) == 1


def test_unlinked_schedule_is_refused_with_the_lessons(client: TestClient):
    register(client)
    schedule_id, teachers = seed_schedule(client, with_ids=False)
    client.put(f"/api/teachers/{teachers['GV']}", json={"first_name": "Guido", "last_name": "X"})

    response = client.post(f"/api/scheduling/schedules/{schedule_id}/swaps/draft", json={})

    assert response.status_code == 409
    assert {l["teacher"] for l in response.json()["detail"]["unlinked"]} == {"GV X"}


def test_invalid_applied_swap_is_refused(client: TestClient):
    register(client)
    schedule_id, teachers = seed_schedule(client)

    response = client.post(
        f"/api/scheduling/schedules/{schedule_id}/swaps/draft",
        json={"applied": [SWAP(teachers), SWAP(teachers)]},
    )

    assert response.status_code == 422
    assert "swap 2" in response.json()["detail"]


def test_save_creates_a_new_schedule_and_keeps_the_origin(client: TestClient):
    register(client)
    schedule_id, teachers = seed_schedule(client)
    origin_before = client.get(f"/api/scheduling/schedules/{schedule_id}").json()

    response = client.post(
        f"/api/scheduling/schedules/{schedule_id}/swaps/save", json={"applied": [SWAP(teachers)]}
    )

    assert response.status_code == 200
    created = response.json()
    assert created["id"] != schedule_id
    assert created["status"] == "MANUAL"
    assert created["nickname"] == "Origine (cambi)"
    assert client.get(f"/api/scheduling/schedules/{schedule_id}").json() == origin_before

    data = client.get(f"/api/scheduling/schedules/{created['id']}").json()["schedule_data"]
    hours = lambda by_class: sorted(
        (name, e["teacher"], e["matter"]) for name, entries in by_class.items() for e in entries
    )
    assert hours(data["by_class"]) == hours(origin_before["schedule_data"]["by_class"])
    assert all("assignment_id" in e for entries in data["by_class"].values() for e in entries)
    assert {(e["teacher"], e["hour"]) for e in data["by_class"]["3A"]} == {
        ("GV X", HOUR_LABELS[0]), ("MR X", HOUR_LABELS[1]),
    }


def test_save_without_swaps_is_refused(client: TestClient):
    register(client)
    schedule_id, _ = seed_schedule(client)

    response = client.post(f"/api/scheduling/schedules/{schedule_id}/swaps/save", json={"applied": []})

    assert response.status_code == 422


def test_swaps_are_isolated_between_workspaces(client: TestClient):
    register(client, "alice")
    schedule_id, teachers = seed_schedule(client)
    register(client, "bob")

    for action in ("draft", "suggest", "save"):
        response = client.post(
            f"/api/scheduling/schedules/{schedule_id}/swaps/{action}",
            json={"applied": [SWAP(teachers)], "teacher_id": teachers["MR"], "slot": {"day": 0, "hour": 1}},
        )
        assert response.status_code == 404
