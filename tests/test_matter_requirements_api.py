"""Requirement validation on writes, and propagation of a matter's defaults."""

from fastapi.testclient import TestClient

from squola.models import MatterRequirements as R


def register(client: TestClient, username: str = "alice") -> None:
    response = client.post(
        "/api/auth/register",
        json={"username": username, "password": f"{username}-password12"},
    )
    assert response.status_code == 201


def make_matter(client: TestClient, name: str, *requirements) -> int:
    response = client.post(
        "/api/matters",
        json={"name": name, "default_requirements": [r.value for r in requirements]},
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def make_class(client: TestClient, section: str = "A") -> int:
    response = client.post("/api/classes", json={"year": "3", "section": section})
    assert response.status_code == 201, response.text
    return response.json()["id"]


def make_teacher(client: TestClient, name: str = "Mario") -> int:
    response = client.post(
        "/api/teachers", json={"first_name": name, "last_name": "Rossi"}
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def make_assignment(
    client: TestClient,
    class_id: int,
    matter_id: int,
    teacher_id: int,
    *requirements,
    hours_per_week: int = 2,
) -> int:
    response = client.post(
        f"/api/classes/{class_id}/assignments",
        json={
            "matter_id": matter_id,
            "teacher_id": teacher_id,
            "hours_per_week": hours_per_week,
            "requirements": [r.value for r in requirements],
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def requirements_of(client: TestClient, class_id: int, assignment_id: int) -> set[str]:
    response = client.get(f"/api/classes/{class_id}")
    assert response.status_code == 200
    for assignment in response.json()["matter_assignments"]:
        if assignment["id"] == assignment_id:
            return set(assignment["requirements"] or [])
    raise AssertionError(f"assignment {assignment_id} not found")


def test_creating_an_assignment_with_an_impossible_combination_is_refused(
    client: TestClient,
):
    register(client)
    matter_id = make_matter(client, "Matematica")
    class_id = make_class(client)
    teacher_id = make_teacher(client)

    response = client.post(
        f"/api/classes/{class_id}/assignments",
        json={
            "matter_id": matter_id,
            "teacher_id": teacher_id,
            "hours_per_week": 3,
            "requirements": [
                R.MAX_TWO_HOURS_PER_DAY.value,
                R.ONE_LESSON_OF_THREE_HOURS_PER_WEEK.value,
            ],
        },
    )

    assert response.status_code == 400
    assert "cannot be scheduled" in response.json()["detail"]
    assert client.get(f"/api/classes/{class_id}").json()["matter_assignments"] == []


def test_creating_an_assignment_whose_weekly_hours_exceed_the_cap_is_refused(
    client: TestClient,
):
    register(client)
    matter_id = make_matter(client, "Matematica")
    class_id = make_class(client)
    teacher_id = make_teacher(client)

    response = client.post(
        f"/api/classes/{class_id}/assignments",
        json={
            "matter_id": matter_id,
            "teacher_id": teacher_id,
            "hours_per_week": 6,
            "requirements": [R.MAX_ONE_HOUR_PER_DAY.value],
        },
    )

    assert response.status_code == 400
    assert client.get(f"/api/classes/{class_id}").json()["matter_assignments"] == []


def test_updating_an_assignment_into_an_impossible_combination_is_refused(
    client: TestClient,
):
    register(client)
    matter_id = make_matter(client, "Matematica")
    class_id = make_class(client)
    teacher_id = make_teacher(client)
    assignment_id = make_assignment(
        client,
        class_id,
        matter_id,
        teacher_id,
        R.ONE_LESSON_OF_THREE_HOURS_PER_WEEK,
        hours_per_week=3,
    )

    response = client.put(
        f"/api/classes/{class_id}/assignments/{assignment_id}",
        json={"requirements": [
            R.MAX_TWO_HOURS_PER_DAY.value,
            R.ONE_LESSON_OF_THREE_HOURS_PER_WEEK.value,
        ]},
    )

    assert response.status_code == 400
    assert requirements_of(client, class_id, assignment_id) == {
        R.ONE_LESSON_OF_THREE_HOURS_PER_WEEK.value
    }


def test_raising_weekly_hours_past_an_existing_cap_is_refused(client: TestClient):
    """The check uses the resulting pair, not only the fields in the request."""
    register(client)
    matter_id = make_matter(client, "Matematica")
    class_id = make_class(client)
    teacher_id = make_teacher(client)
    assignment_id = make_assignment(
        client, class_id, matter_id, teacher_id, R.MAX_ONE_HOUR_PER_DAY
    )

    response = client.put(
        f"/api/classes/{class_id}/assignments/{assignment_id}",
        json={"hours_per_week": 6},
    )

    assert response.status_code == 400


def test_a_legal_assignment_update_still_works(client: TestClient):
    register(client)
    matter_id = make_matter(client, "Matematica")
    class_id = make_class(client)
    teacher_id = make_teacher(client)
    assignment_id = make_assignment(client, class_id, matter_id, teacher_id)

    response = client.put(
        f"/api/classes/{class_id}/assignments/{assignment_id}",
        json={
            "hours_per_week": 10,
            "requirements": [
                R.MAX_TWO_HOURS_PER_DAY.value,
                R.ONE_LESSON_OF_TWO_HOURS_PER_WEEK.value,
            ],
        },
    )

    assert response.status_code == 200, response.text
    assert requirements_of(client, class_id, assignment_id) == {
        R.MAX_TWO_HOURS_PER_DAY.value,
        R.ONE_LESSON_OF_TWO_HOURS_PER_WEEK.value,
    }


def test_creating_a_matter_with_impossible_defaults_is_refused(client: TestClient):
    register(client)

    response = client.post(
        "/api/matters",
        json={
            "name": "Matematica",
            "default_requirements": [
                R.MAX_ONE_HOUR_PER_DAY.value,
                R.ONE_LESSON_OF_TWO_HOURS_PER_WEEK.value,
            ],
        },
    )

    assert response.status_code == 400
    assert "cannot be scheduled" in response.json()["detail"]
    assert client.get("/api/matters").json() == []


def test_a_default_added_to_a_matter_reaches_its_existing_assignments(
    client: TestClient,
):
    register(client)
    matter_id = make_matter(client, "Matematica", R.AT_LEAST_TWICE_PER_WEEK)
    class_id = make_class(client)
    teacher_id = make_teacher(client)
    assignment_id = make_assignment(
        client,
        class_id,
        matter_id,
        teacher_id,
        R.AT_LEAST_TWICE_PER_WEEK,
        R.ONE_LESSON_OF_TWO_HOURS_PER_WEEK,
    )

    response = client.put(
        f"/api/matters/{matter_id}",
        json={
            "default_requirements": [
                R.AT_LEAST_TWICE_PER_WEEK.value,
                R.MAX_TWO_HOURS_PER_DAY.value,
            ]
        },
    )

    assert response.status_code == 200, response.text
    assert requirements_of(client, class_id, assignment_id) == {
        R.AT_LEAST_TWICE_PER_WEEK.value,
        R.ONE_LESSON_OF_TWO_HOURS_PER_WEEK.value,
        R.MAX_TWO_HOURS_PER_DAY.value,
    }


def test_a_default_removed_from_a_matter_is_removed_from_its_assignments(
    client: TestClient,
):
    register(client)
    matter_id = make_matter(
        client, "Matematica", R.AT_LEAST_TWICE_PER_WEEK, R.MAX_TWO_HOURS_PER_DAY
    )
    class_id = make_class(client)
    teacher_id = make_teacher(client)
    assignment_id = make_assignment(
        client,
        class_id,
        matter_id,
        teacher_id,
        R.AT_LEAST_TWICE_PER_WEEK,
        R.ONE_LESSON_OF_TWO_HOURS_PER_WEEK,
        R.MAX_TWO_HOURS_PER_DAY,
    )

    response = client.put(
        f"/api/matters/{matter_id}",
        json={"default_requirements": [R.AT_LEAST_TWICE_PER_WEEK.value]},
    )

    assert response.status_code == 200, response.text
    assert requirements_of(client, class_id, assignment_id) == {
        R.AT_LEAST_TWICE_PER_WEEK.value,
        R.ONE_LESSON_OF_TWO_HOURS_PER_WEEK.value,
    }


def test_a_requirement_outside_the_delta_survives_propagation(client: TestClient):
    """one_lesson_of_two_hours is on the assignment alone, and stays there."""
    register(client)
    matter_id = make_matter(client, "Matematica")
    class_id = make_class(client)
    teacher_id = make_teacher(client)
    assignment_id = make_assignment(
        client, class_id, matter_id, teacher_id, R.ONE_LESSON_OF_TWO_HOURS_PER_WEEK
    )

    add = client.put(
        f"/api/matters/{matter_id}",
        json={"default_requirements": [R.AT_LEAST_TWICE_PER_WEEK.value]},
    )
    assert add.status_code == 200
    remove = client.put(
        f"/api/matters/{matter_id}", json={"default_requirements": []}
    )
    assert remove.status_code == 200

    assert requirements_of(client, class_id, assignment_id) == {
        R.ONE_LESSON_OF_TWO_HOURS_PER_WEEK.value
    }


def test_updating_a_matter_without_touching_its_defaults_leaves_assignments_alone(
    client: TestClient,
):
    register(client)
    matter_id = make_matter(client, "Matematica", R.AT_LEAST_TWICE_PER_WEEK)
    class_id = make_class(client)
    teacher_id = make_teacher(client)
    assignment_id = make_assignment(
        client, class_id, matter_id, teacher_id, R.ONE_LESSON_OF_TWO_HOURS_PER_WEEK
    )

    response = client.put(f"/api/matters/{matter_id}", json={"name": "Mate"})

    assert response.status_code == 200, response.text
    assert requirements_of(client, class_id, assignment_id) == {
        R.ONE_LESSON_OF_TWO_HOURS_PER_WEEK.value
    }


def test_setting_defaults_on_a_matter_with_no_assignments(client: TestClient):
    register(client)
    matter_id = make_matter(client, "Matematica")

    response = client.put(
        f"/api/matters/{matter_id}",
        json={"default_requirements": [R.MAX_TWO_HOURS_PER_DAY.value]},
    )

    assert response.status_code == 200, response.text
    assert response.json()["default_requirements"] == [R.MAX_TWO_HOURS_PER_DAY.value]


def test_propagation_touches_only_assignments_of_that_matter(client: TestClient):
    register(client)
    capped_matter = make_matter(client, "Matematica")
    other_matter = make_matter(client, "Storia")
    class_id = make_class(client)
    teacher_id = make_teacher(client)
    capped_assignment = make_assignment(
        client, class_id, capped_matter, teacher_id, hours_per_week=4
    )
    other_assignment = make_assignment(
        client, class_id, other_matter, teacher_id, hours_per_week=4
    )

    response = client.put(
        f"/api/matters/{capped_matter}",
        json={"default_requirements": [R.MAX_TWO_HOURS_PER_DAY.value]},
    )

    assert response.status_code == 200, response.text
    assert requirements_of(client, class_id, capped_assignment) == {
        R.MAX_TWO_HOURS_PER_DAY.value
    }
    assert requirements_of(client, class_id, other_assignment) == set()


def test_a_push_conflicting_with_an_assignment_is_refused_whole(client: TestClient):
    register(client)
    matter_id = make_matter(client, "Matematica")
    class_id = make_class(client)
    teacher_id = make_teacher(client)
    safe = make_assignment(client, class_id, matter_id, teacher_id, hours_per_week=4)

    other_class = make_class(client, section="B")
    conflicting = make_assignment(
        client,
        other_class,
        matter_id,
        teacher_id,
        R.ONE_LESSON_OF_THREE_HOURS_PER_WEEK,
        hours_per_week=3,
    )

    response = client.put(
        f"/api/matters/{matter_id}",
        json={"default_requirements": [R.MAX_TWO_HOURS_PER_DAY.value]},
    )

    assert response.status_code == 400
    assert f"assignment {conflicting}" in response.json()["detail"]
    assert client.get(f"/api/matters/{matter_id}").json()["default_requirements"] == []
    assert requirements_of(client, class_id, safe) == set()
    assert requirements_of(client, other_class, conflicting) == {
        R.ONE_LESSON_OF_THREE_HOURS_PER_WEEK.value
    }


def test_a_push_that_overruns_weekly_hours_is_refused(client: TestClient):
    register(client)
    matter_id = make_matter(client, "Matematica")
    class_id = make_class(client)
    teacher_id = make_teacher(client)
    assignment_id = make_assignment(
        client, class_id, matter_id, teacher_id, hours_per_week=6
    )

    response = client.put(
        f"/api/matters/{matter_id}",
        json={"default_requirements": [R.MAX_ONE_HOUR_PER_DAY.value]},
    )

    assert response.status_code == 400
    assert requirements_of(client, class_id, assignment_id) == set()
    assert client.get(f"/api/matters/{matter_id}").json()["default_requirements"] == []
