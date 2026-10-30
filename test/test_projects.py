import pytest


def create_project(client):
    response = client.post(
        "/v1/projects",
        json={
            "name": "Учебный проект",
            "description": "Описание проекта",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_project_crud(client):
    project = create_project(client)
    path = f"/v1/projects/{project['id']}"

    assert project["name"] == "Учебный проект"
    assert project["created_at"]

    response = client.get(path)
    assert response.status_code == 200
    assert response.json() == project

    response = client.get("/v1/projects")
    assert response.status_code == 200
    assert any(
        item["id"] == project["id"]
        for item in response.json()
    )

    response = client.patch(
        path,
        json={"name": "Новое название"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Новое название"
    assert response.json()["description"] == "Описание проекта"

    response = client.patch(
        path,
        json={"description": None},
    )
    assert response.status_code == 200
    assert response.json()["description"] is None

    response = client.delete(path)
    assert response.status_code == 204
    assert response.content == b""

    assert client.get(path).status_code == 404


def test_project_without_description(client):
    response = client.post(
        "/v1/projects",
        json={"name": "Без описания"},
    )

    assert response.status_code == 201
    assert response.json()["description"] is None


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"name": ""},
        {"name": "   "},
        {"name": "А" * 201},
        {"name": "Проект", "id": 100},
        {"name": "Проект", "created_at": "2026-01-01"},
    ],
)
def test_invalid_project(client, payload):
    response = client.post("/v1/projects", json=payload)

    assert response.status_code == 422


def test_project_update_rejects_null_name(client):
    project = create_project(client)

    response = client.patch(
        f"/v1/projects/{project['id']}",
        json={"name": None},
    )

    assert response.status_code == 422


def test_missing_project(client):
    project = create_project(client)
    path = f"/v1/projects/{project['id']}"

    assert client.delete(path).status_code == 204
    assert client.get(path).status_code == 404
    assert client.patch(path, json={}).status_code == 404
    assert client.delete(path).status_code == 404