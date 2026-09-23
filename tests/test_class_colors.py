import re

from fastapi.testclient import TestClient

from squola.models import CLASS_COLOR_PALETTE


def contrast_with_black(hex_color: str) -> float:
    channels = [int(hex_color[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    r, g, b = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return (0.2126 * r + 0.7152 * g + 0.0722 * b + 0.05) / 0.05


def register(client: TestClient, username: str):
    return client.post("/api/auth/register", json={"username": username, "password": f"{username}-password12"})


def create_class(client: TestClient, year: str, section: str, **extra):
    return client.post("/api/classes", json={"year": year, "section": section, **extra})


def test_palette_is_distinct_and_readable():
    assert len(CLASS_COLOR_PALETTE) == len(set(CLASS_COLOR_PALETTE)) == 30
    for color in CLASS_COLOR_PALETTE:
        assert re.fullmatch(r"#[0-9a-f]{6}", color)
        assert contrast_with_black(color) >= 4.5, color


def test_default_colors_are_distinct_and_skip_used(client: TestClient):
    register(client, "alice")
    first = create_class(client, "1", "A").json()
    second = create_class(client, "1", "B").json()
    assert [first["color"], second["color"]] == CLASS_COLOR_PALETTE[:2]

    client.delete(f"/api/classes/{first['id']}")
    third = create_class(client, "1", "C").json()
    assert third["color"] == CLASS_COLOR_PALETTE[0]

    clone = client.post(f"/api/classes/{third['id']}/clone", json={"year": "1", "section": "D"}).json()
    assert clone["color"] == CLASS_COLOR_PALETTE[2]


def test_all_thirty_classes_get_distinct_defaults(client: TestClient):
    register(client, "alice")
    colors = {
        create_class(client, year, section).json()["color"]
        for year in "12345"
        for section in "ABCDEF"
    }
    assert colors == set(CLASS_COLOR_PALETTE)


def test_default_colors_are_per_workspace(client: TestClient):
    register(client, "alice")
    create_class(client, "1", "A")
    register(client, "bob")
    assert create_class(client, "1", "A").json()["color"] == CLASS_COLOR_PALETTE[0]


def test_update_color_accepts_duplicates_and_rejects_invalid(client: TestClient):
    register(client, "alice")
    first = create_class(client, "1", "A").json()
    second = create_class(client, "1", "B").json()

    updated = client.put(f"/api/classes/{second['id']}", json={"color": first["color"].upper()})
    assert updated.status_code == 200
    assert updated.json()["color"] == first["color"]

    invalid = client.put(f"/api/classes/{second['id']}", json={"color": "red"})
    assert invalid.status_code == 422
    assert client.get(f"/api/classes/{second['id']}").json()["color"] == first["color"]

    assert create_class(client, "1", "C", color="#12345").status_code == 422
