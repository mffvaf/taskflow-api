import pytest


def create_label(client):
    response = client.post(
        "/v1/labels",
        json={"name": "Важно", "color": "#ff8800"},
    )
    assert response.status_code == 201
    return response.json()


def test_label_crud(client):
    label = create_label(client)
    path = f"/v1/labels/{label['id']}"

    assert label["name"] == "Важно"
    assert label["color"] == "#ff8800"

    response = client.get(path)
    assert response.status_code == 200
    assert response.json() == label

    response = client.get("/v1/labels")
    assert response.status_code == 200
    assert any(
        item["id"] == label["id"]
        for item in response.json()
    )

    response = client.patch(
        path,
        json={"color": "#AABBCC"},
    )
    assert response.status_code == 200
    assert response.json()["color"] == "#AABBCC"
    assert response.json()["name"] == "Важно"

    response = client.delete(path)
    assert response.status_code == 204
    assert response.content == b""

    assert client.get(path).status_code == 404


def test_default_label_color(client):
    response = client.post(
        "/v1/labels",
        json={"name": "Обычная"},
    )

    assert response.status_code == 201
    assert response.json()["color"] == "#6b7280"


def test_duplicate_label_name(client):
    create_label(client)

    response = client.post(
        "/v1/labels",
        json={"name": "Важно"},
    )

    assert response.status_code == 409


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"name": ""},
        {"name": "   "},
        {"name": "А" * 65},
        {"name": "Метка", "color": "red"},
        {"name": "Метка", "color": "#12345"},
        {"name": "Метка", "color": "#GGGGGG"},
        {"name": "Метка", "id": 100},
    ],
)
def test_invalid_label(client, payload):
    response = client.post("/v1/labels", json=payload)

    assert response.status_code == 422


@pytest.mark.parametrize("field", ["name", "color"])
def test_label_update_rejects_null(client, field):
    label = create_label(client)

    response = client.patch(
        f"/v1/labels/{label['id']}",
        json={field: None},
    )

    assert response.status_code == 422


def test_missing_label(client):
    label = create_label(client)
    path = f"/v1/labels/{label['id']}"

    assert client.delete(path).status_code == 204
    assert client.get(path).status_code == 404
    assert client.patch(path, json={}).status_code == 404
    assert client.delete(path).status_code == 404