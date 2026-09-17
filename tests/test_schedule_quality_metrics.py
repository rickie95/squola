"""Quality diagnostics reported alongside a generated timetable."""

from fastapi.testclient import TestClient

from squola.scheduler import QUALITY_DIMENSIONS, ScheduleSlot, compute_quality_metrics


def slot(day: int, hour: int, class_id: int, teacher: str = "Azzurra Lami"):
    return ScheduleSlot(
        day=day,
        hour=hour,
        class_id=class_id,
        class_name=f"{class_id}C",
        teacher_id=1 if teacher == "Azzurra Lami" else 2,
        teacher_name=teacher,
        matter_id=1,
        matter_name="Matematica",
        assignment_id=class_id,
    )


def test_worst_offenders_rank_the_churning_day_first():
    """Lami: 3C 2C 3C 2C on Monday, a tidy Tuesday for a second teacher."""
    slots = [
        slot(0, 1, 3), slot(0, 2, 2), slot(0, 3, 3), slot(0, 4, 2),
        slot(1, 1, 3, "Alba Grazia"), slot(1, 2, 3, "Alba Grazia"),
    ]

    worst = compute_quality_metrics(slots, {1: 5, 2: 5})["worst"]["class_blocks"]

    assert worst[0] == {"teacher": "Azzurra Lami", "day": "Monday", "value": 2}
    assert len(worst) == 1


def test_generation_reports_quality_metrics(client: TestClient):
    client.post("/api/auth/register", json={"username": "alice", "password": "alice-password12"})
    matter_id = client.post(
        "/api/matters", json={"name": "Matematica", "default_requirements": []}
    ).json()["id"]
    teacher_id = client.post(
        "/api/teachers",
        json={
            "first_name": "Alice",
            "last_name": "Rossi",
            "email": None,
            "schedule_preference": "none",
            "matter_ids": [matter_id],
        },
    ).json()["id"]
    class_id = client.post("/api/classes", json={"year": "I", "section": "A"}).json()["id"]
    client.post(
        f"/api/classes/{class_id}/assignments",
        json={
            "matter_id": matter_id,
            "teacher_id": teacher_id,
            "hours_per_week": 10,
            "requirements": [],
        },
    )

    generated = client.post("/api/scheduling/generate", json={"time_limit_seconds": 3})
    assert generated.status_code == 200

    quality = generated.json()["metadata"]["quality"]
    for dimension in QUALITY_DIMENSIONS:
        assert isinstance(quality[dimension], int)
        assert isinstance(quality["worst"][dimension], list)

    # 5.4: the saved copy carries no metrics.
    schedule_id = client.get("/api/scheduling/schedules").json()[0]["id"]
    saved = client.get(f"/api/scheduling/schedules/{schedule_id}")
    assert saved.status_code == 200
    assert "quality" not in saved.text


def test_generation_without_data_reports_no_metrics(client: TestClient):
    client.post("/api/auth/register", json={"username": "bob", "password": "bob-password-123"})

    generated = client.post("/api/scheduling/generate", json={"time_limit_seconds": 3})

    assert generated.status_code == 400
    assert "quality" not in generated.text
