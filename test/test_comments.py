import pytest


@pytest.fixture()
def comment_data(client):
    response = client.post(
        "/v1/users",
        json={
            "email": "author@example.com",
            "display_name": "Автор",
        },
    )
    assert response.status_code == 201
    author = response.json()

    response = client.post(
        "/v1/projects",
        json={"name": "Проект комментариев"},
    )
    assert response.status_code == 201
    project = response.json()

    response = client.post(
        "/v1/tasks",
        json={
            "project_id": project["id"],
            "title": "Задача с комментариями",
        },
    )
    assert response.status_code == 201
    task = response.json()

    return {
        "author_id": author["id"],
        "task_id": task["id"],
        "project_id": project["id"],
    }


def create_comment(client, data, body="Первый комментарий"):
    response = client.post(
        "/v1/comments",
        json={
            "task_id": data["task_id"],
            "author_id": data["author_id"],
            "body": body,
        },
    )
    assert response.status_code == 201
    return response.json()


def test_comment_crud(client, comment_data):
    comment = create_comment(client, comment_data)
    path = f"/v1/comments/{comment['id']}"

    assert comment["body"] == "Первый комментарий"
    assert comment["created_at"]

    response = client.get(path)
    assert response.status_code == 200
    assert response.json() == comment

    response = client.get("/v1/comments")
    assert response.status_code == 200
    assert any(
        item["id"] == comment["id"]
        for item in response.json()
    )

    response = client.patch(
        path,
        json={"body": "Исправленный комментарий"},
    )
    assert response.status_code == 200

    updated = response.json()
    assert updated["body"] == "Исправленный комментарий"
    assert updated["task_id"] == comment["task_id"]
    assert updated["author_id"] == comment["author_id"]
    assert updated["created_at"] == comment["created_at"]

    response = client.delete(path)
    assert response.status_code == 204
    assert response.content == b""

    assert client.get(path).status_code == 404


def test_comment_filter(client, comment_data):
    first = create_comment(client, comment_data)
    second = create_comment(
        client,
        comment_data,
        body="Второй комментарий",
    )

    response = client.post(
        "/v1/tasks",
        json={
            "project_id": comment_data["project_id"],
            "title": "Другая задача",
        },
    )
    assert response.status_code == 201
    other_task = response.json()

    other_data = {
        **comment_data,
        "task_id": other_task["id"],
    }
    create_comment(client, other_data)

    response = client.get(
        "/v1/comments",
        params={"task_id": comment_data["task_id"]},
    )

    assert response.status_code == 200
    assert {item["id"] for item in response.json()} == {
        first["id"],
        second["id"],
    }


@pytest.mark.parametrize(
    "changes",
    [
        {"body": ""},
        {"body": "   "},
        {"body": None},
        {"task_id": 0},
        {"author_id": -1},
        {"id": 100},
        {"created_at": "2026-01-01"},
    ],
)
def test_invalid_comment(client, comment_data, changes):
    payload = {
        "task_id": comment_data["task_id"],
        "author_id": comment_data["author_id"],
        "body": "Комментарий",
    }
    payload.update(changes)

    response = client.post("/v1/comments", json=payload)

    assert response.status_code == 422


@pytest.mark.parametrize(
    "field",
    ["task_id", "author_id", "body"],
)
def test_comment_update_rejects_null(
    client,
    comment_data,
    field,
):
    comment = create_comment(client, comment_data)

    response = client.patch(
        f"/v1/comments/{comment['id']}",
        json={field: None},
    )

    assert response.status_code == 422


def test_comment_missing_author(client, comment_data):
    author_id = comment_data["author_id"]

    assert client.delete(
        f"/v1/users/{author_id}"
    ).status_code == 204

    response = client.post(
        "/v1/comments",
        json={
            "task_id": comment_data["task_id"],
            "author_id": author_id,
            "body": "Автор не существует",
        },
    )

    assert response.status_code == 409


def test_comment_missing_task(client, comment_data):
    task_id = comment_data["task_id"]

    assert client.delete(
        f"/v1/tasks/{task_id}"
    ).status_code == 204

    response = client.post(
        "/v1/comments",
        json={
            "task_id": task_id,
            "author_id": comment_data["author_id"],
            "body": "Задача не существует",
        },
    )

    assert response.status_code == 409


def test_missing_comment(client, comment_data):
    comment = create_comment(client, comment_data)
    path = f"/v1/comments/{comment['id']}"

    assert client.delete(path).status_code == 204
    assert client.get(path).status_code == 404
    assert client.patch(path, json={}).status_code == 404
    assert client.delete(path).status_code == 404