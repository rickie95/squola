from fastapi.testclient import TestClient


def register(client: TestClient, username: str, password: str):
    return client.post(
        "/api/auth/register",
        json={"username": username, "password": password},
    )


def login(client: TestClient, username: str, password: str):
    return client.post(
        "/api/auth/login",
        json={"username": username, "password": password},
    )


def test_auth_register_login_logout_me(client: TestClient):
    register_response = register(client, "alice", "supersecure123")
    assert register_response.status_code == 201
    register_data = register_response.json()
    assert register_data["user"]["username"] == "alice"
    assert "workspace" in register_data

    me_response = client.get("/api/auth/me")
    assert me_response.status_code == 200
    assert me_response.json()["user"]["username"] == "alice"

    logout_response = client.post("/api/auth/logout")
    assert logout_response.status_code == 204

    me_after_logout = client.get("/api/auth/me")
    assert me_after_logout.status_code == 401

    bad_login = login(client, "alice", "wrong-password")
    assert bad_login.status_code == 401
    assert bad_login.json()["detail"] == "Invalid credentials"

    good_login = login(client, "alice", "supersecure123")
    assert good_login.status_code == 200
    assert good_login.json()["user"]["username"] == "alice"


def test_account_password_and_workspace_update(client: TestClient):
    register(client, "franco", "passwordlunga12")

    rename_workspace = client.patch("/api/account/workspace", json={"name": "Liceo Franco"})
    assert rename_workspace.status_code == 200
    assert rename_workspace.json()["workspace"]["name"] == "Liceo Franco"

    change_password = client.patch(
        "/api/account/password",
        json={"current_password": "passwordlunga12", "new_password": "password-nuova-123"},
    )
    assert change_password.status_code == 204

    # Sessions are revoked after password change.
    me_after_change = client.get("/api/auth/me")
    assert me_after_change.status_code == 401

    old_password_login = login(client, "franco", "passwordlunga12")
    assert old_password_login.status_code == 401

    new_password_login = login(client, "franco", "password-nuova-123")
    assert new_password_login.status_code == 200

