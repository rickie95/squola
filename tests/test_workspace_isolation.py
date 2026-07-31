from fastapi.testclient import TestClient


def register(client: TestClient, username: str, password: str):
    return client.post("/api/auth/register", json={"username": username, "password": password})


def login(client: TestClient, username: str, password: str):
    return client.post("/api/auth/login", json={"username": username, "password": password})


def test_protected_endpoints_require_auth(client: TestClient):
    response = client.get("/api/teachers")
    assert response.status_code == 401


def test_workspace_data_isolation(client: TestClient):
    register(client, "alice", "alice-password12")

    matter_id = client.post(
        "/api/matters",
        json={"name": "Matematica", "default_requirements": []},
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
    assignment_id = client.post(
        f"/api/classes/{class_id}/assignments",
        json={
            "matter_id": matter_id,
            "teacher_id": teacher_id,
            "hours_per_week": 1,
            "requirements": [],
        },
    ).json()["id"]

    generated = client.post("/api/scheduling/generate", json={"time_limit_seconds": 3})
    assert generated.status_code == 200
    assert generated.json()["metadata"]["status"] in {"OPTIMAL", "FEASIBLE"}

    alice_schedules = client.get("/api/scheduling/schedules")
    assert alice_schedules.status_code == 200
    assert len(alice_schedules.json()) == 1

    client.post("/api/auth/logout")
    register(client, "bob", "bob-password-123")

    assert client.get(f"/api/teachers/{teacher_id}").status_code == 404
    assert client.get(f"/api/classes/{class_id}").status_code == 404
    assert client.get(f"/api/classes/{class_id}/assignments").status_code == 404
    assert client.get("/api/scheduling/schedules").json() == []

    cross_delete_teacher = client.delete(f"/api/teachers/{teacher_id}")
    assert cross_delete_teacher.status_code == 404

    cross_update_assignment = client.put(
        f"/api/classes/{class_id}/assignments/{assignment_id}",
        json={"hours_per_week": 2},
    )
    assert cross_update_assignment.status_code == 404

