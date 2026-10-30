from datetime import datetime

import pytest


@pytest.fixture()
def project(client):
    response = client.post(
        "/v1/projects",
        json={"name": "Проект для тестов задач"},
    )
    assert response.status_code == 201
    return response.json()


def create_task(client, project_id, **fields):
    payload = {
        "project_id": project_id,
        "title": "Тестовая задача",
    }
    payload.update(fields)

    response = client.post("/v1/tasks", json=payload)
    assert response.status_code == 201
    return response.json()


def test_task_crud(client, project):
    task = create_task(client, project["id"])
    path = f"/v1/tasks/{task['id']}"

    assert task["status"] == "open"
    assert task["priority"] == "medium"
    assert task["assignee_id"] is None
    assert task["label_id"] is None
    assert task["created_at"]
    assert task["updated_at"]

    response = client.get(path)
    assert response.status_code == 200
    assert response.json() == task

    response = client.get("/v1/tasks")
    assert response.status_code == 200
    assert any(
        item["id"] == task["id"]
        for item in response.json()
    )

    response = client.patch(
        path,
        json={"status": "done"},
    )
    assert response.status_code == 200

    updated = response.json()
    assert updated["status"] == "done"
    assert updated["title"] == task["title"]
    assert updated["project_id"] == project["id"]
    assert updated["created_at"] == task["created_at"]

    old_time = datetime.fromisoformat(task["updated_at"])
    new_time = datetime.fromisoformat(updated["updated_at"])
    assert new_time > old_time

    response = client.delete(path)
    assert response.status_code == 204
    assert response.content == b""

    assert client.get(path).status_code == 404


def test_task_filters(client, project):
    second_project = client.post(
        "/v1/projects",
        json={"name": "Другой проект"},
    ).json()

    opened = create_task(client, project["id"])
    done = create_task(
        client,
        project["id"],
        status="done",
    )
    other = create_task(client, second_project["id"])

    response = client.get(
        "/v1/tasks",
        params={"project_id": project["id"]},
    )
    assert response.status_code == 200
    assert {item["id"] for item in response.json()} == {
        opened["id"],
        done["id"],
    }

    response = client.get(
        "/v1/tasks",
        params={
            "project_id": project["id"],
            "status": "open",
        },
    )
    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [
        opened["id"]
    ]

    response = client.get(
        "/v1/tasks",
        params={"status": "open"},
    )
    assert response.status_code == 200
    ids = {item["id"] for item in response.json()}
    assert opened["id"] in ids
    assert other["id"] in ids
    assert done["id"] not in ids


@pytest.mark.parametrize(
    "changes",
    [
        {"title": ""},
        {"title": "   "},
        {"title": "А" * 201},
        {"status": "unknown"},
        {"priority": "urgent"},
        {"project_id": 0},
        {"assignee_id": -1},
        {"id": 100},
        {"updated_at": "2026-01-01"},
    ],
)
def test_invalid_task(client, project, changes):
    payload = {
        "project_id": project["id"],
        "title": "Задача",
    }
    payload.update(changes)

    response = client.post("/v1/tasks", json=payload)

    assert response.status_code == 422


@pytest.mark.parametrize(
    "field",
    ["project_id", "title", "status", "priority"],
)
def test_task_update_rejects_null(client, project, field):
    task = create_task(client, project["id"])

    response = client.patch(
        f"/v1/tasks/{task['id']}",
        json={field: None},
    )

    assert response.status_code == 422


def test_task_missing_project(client):
    response = client.post(
        "/v1/projects",
        json={"name": "Временный проект"},
    )
    assert response.status_code == 201
    project_id = response.json()["id"]

    assert client.delete(
        f"/v1/projects/{project_id}"
    ).status_code == 204

    response = client.post(
        "/v1/tasks",
        json={
            "project_id": project_id,
            "title": "Несуществующий проект",
        },
    )

    assert response.status_code == 409


def test_missing_task(client, project):
    task = create_task(client, project["id"])
    path = f"/v1/tasks/{task['id']}"

    assert client.delete(path).status_code == 204
    assert client.get(path).status_code == 404
    assert client.patch(path, json={}).status_code == 404
    assert client.delete(path).status_code == 404


def test_invalid_task_filter(client):
    response = client.get(
        "/v1/tasks",
        params={"status": "unknown"},
    )

    assert response.status_code == 422