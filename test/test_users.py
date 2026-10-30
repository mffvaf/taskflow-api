import pytest


def create_user(client):
    response = client.post(
        "/v1/users",
        json={
            "email": "anna@example.com",
            "display_name": "Анна",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_user_crud(client):
    user = create_user(client)
    user_id = user["id"]

    assert user["email"] == "anna@example.com"
    assert user["display_name"] == "Анна"
    assert user["role"] == "operator"
    assert user["created_at"]

    response = client.get(f"/v1/users/{user_id}")
    assert response.status_code == 200
    assert response.json() == user

    response = client.get("/v1/users")
    assert response.status_code == 200
    assert any(
        item["id"] == user_id
        for item in response.json()
    )

    response = client.patch(
        f"/v1/users/{user_id}",
        json={"display_name": "Дарья"},
    )
    assert response.status_code == 200
    assert response.json()["display_name"] == "Дарья"
    assert response.json()["email"] == user["email"]

    response = client.delete(f"/v1/users/{user_id}")
    assert response.status_code == 204
    assert response.content == b""

    response = client.get(f"/v1/users/{user_id}")
    assert response.status_code == 404


def test_duplicate_email(client):
    create_user(client)

    response = client.post(
        "/v1/users",
        json={
            "email": "anna@example.com",
            "display_name": "Другой пользователь",
        },
    )

    assert response.status_code == 409


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"email": "wrong", "display_name": "Анна"},
        {"email": "anna@example.com", "display_name": ""},
        {
            "email": "anna@example.com",
            "display_name": "Анна",
            "role": "unknown",
        },
        {
            "email": "anna@example.com",
            "display_name": "Анна",
            "id": 100,
        },
    ],
)
def test_invalid_user(client, payload):
    response = client.post("/v1/users", json=payload)

    assert response.status_code == 422


def test_user_update_rejects_null(client):
    user = create_user(client)

    response = client.patch(
        f"/v1/users/{user['id']}",
        json={"display_name": None},
    )

    assert response.status_code == 422


def test_missing_user(client):
    # Создаём и удаляем запись, чтобы точно получить
    # несуществующий id без предположений о счётчике.
    user = create_user(client)
    path = f"/v1/users/{user['id']}"

    assert client.delete(path).status_code == 204
    assert client.get(path).status_code == 404
    assert client.patch(path, json={}).status_code == 404
    assert client.delete(path).status_code == 404