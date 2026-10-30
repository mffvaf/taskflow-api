import pytest


@pytest.fixture()
def records(client):
    def create(resource, payload):
        response = client.post(
            f"/v1/{resource}",
            json=payload,
        )
        assert response.status_code == 201
        return response.json()

    user = create(
        "users",
        {
            "email": "relations@example.com",
            "display_name": "Исполнитель",
        },
    )
    project = create("projects", {"name": "Проверка связей"})
    label = create("labels", {"name": "Тестовая метка"})

    task = create(
        "tasks",
        {
            "project_id": project["id"],
            "assignee_id": user["id"],
            "label_id": label["id"],
            "title": "Проверка удаления",
        },
    )
    comment = create(
        "comments",
        {
            "task_id": task["id"],
            "author_id": user["id"],
            "body": "Тестовый комментарий",
        },
    )

    return {
        "user": user,
        "project": project,
        "label": label,
        "task": task,
        "comment": comment,
    }


def test_delete_project_cascades(client, records):
    project_id = records["project"]["id"]
    task_id = records["task"]["id"]
    comment_id = records["comment"]["id"]

    response = client.delete(f"/v1/projects/{project_id}")

    assert response.status_code == 204
    assert client.get(
        f"/v1/tasks/{task_id}"
    ).status_code == 404
    assert client.get(
        f"/v1/comments/{comment_id}"
    ).status_code == 404

    # Пользователь и метка должны сохраниться.
    assert client.get(
        f"/v1/users/{records['user']['id']}"
    ).status_code == 200
    assert client.get(
        f"/v1/labels/{records['label']['id']}"
    ).status_code == 200


def test_delete_task_cascades(client, records):
    task_id = records["task"]["id"]
    comment_id = records["comment"]["id"]

    response = client.delete(f"/v1/tasks/{task_id}")

    assert response.status_code == 204
    assert client.get(
        f"/v1/comments/{comment_id}"
    ).status_code == 404
    assert client.get(
        f"/v1/projects/{records['project']['id']}"
    ).status_code == 200


def test_cannot_delete_comment_author(client, records):
    user_id = records["user"]["id"]

    response = client.delete(f"/v1/users/{user_id}")

    assert response.status_code == 409

    # После конфликта записи остаются доступными.
    assert client.get(
        f"/v1/users/{user_id}"
    ).status_code == 200
    assert client.get(
        f"/v1/comments/{records['comment']['id']}"
    ).status_code == 200


def test_delete_assignee_sets_null(client, records):
    user_id = records["user"]["id"]
    task_id = records["task"]["id"]
    comment_id = records["comment"]["id"]

    # Сначала удаляем комментарий, иначе автора
    # нельзя удалить из-за ограничения RESTRICT.
    assert client.delete(
        f"/v1/comments/{comment_id}"
    ).status_code == 204

    assert client.delete(
        f"/v1/users/{user_id}"
    ).status_code == 204

    response = client.get(f"/v1/tasks/{task_id}")

    assert response.status_code == 200
    assert response.json()["assignee_id"] is None
    assert response.json()["label_id"] == records["label"]["id"]


def test_delete_label_sets_null(client, records):
    label_id = records["label"]["id"]
    task_id = records["task"]["id"]

    assert client.delete(
        f"/v1/labels/{label_id}"
    ).status_code == 204

    response = client.get(f"/v1/tasks/{task_id}")

    assert response.status_code == 200
    assert response.json()["label_id"] is None
    assert response.json()["assignee_id"] == records["user"]["id"]


@pytest.mark.parametrize(
    "resource,record_name,field",
    [
        ("users", "user", "assignee_id"),
        ("labels", "label", "label_id"),
    ],
)
def test_task_rejects_missing_relation(
    client,
    records,
    resource,
    record_name,
    field,
):
    comment_id = records["comment"]["id"]
    missing_id = records[record_name]["id"]
    task_id = records["task"]["id"]

    assert client.delete(
        f"/v1/comments/{comment_id}"
    ).status_code == 204
    assert client.delete(
        f"/v1/{resource}/{missing_id}"
    ).status_code == 204

    # Нельзя создать задачу с удалённой связанной записью.
    response = client.post(
        "/v1/tasks",
        json={
            "project_id": records["project"]["id"],
            "title": "Некорректная связь",
            field: missing_id,
        },
    )
    assert response.status_code == 409

    # Нельзя установить такую связь через PATCH.
    response = client.patch(
        f"/v1/tasks/{task_id}",
        json={field: missing_id},
    )
    assert response.status_code == 409

    # Неудачное обновление не должно изменить задачу.
    response = client.get(f"/v1/tasks/{task_id}")
    assert response.status_code == 200
    assert response.json()[field] is None