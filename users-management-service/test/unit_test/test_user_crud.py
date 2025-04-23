import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
def test_create_user():
    client = APIClient()
    response = client.post(
        "/api/users/",
        {
            "username": "testuser",
            "password": "strongpass123",
            "email": "test@example.com",
        },
        format="json",
    )
    assert response.status_code == 201
    assert response.data["username"] == "testuser"


@pytest.mark.django_db
def test_get_user_list(authenticated_client):
    response = authenticated_client.get("/api/users/")
    assert response.status_code == 200
    assert isinstance(response.data, list)


@pytest.mark.django_db
def test_update_user(authenticated_client, created_user):
    user_id = created_user.id
    response = authenticated_client.put(
        f"/api/users/{user_id}/",
        {
            "username": "updateduser",
            "email": "updated@example.com",
            "password": "newstrongpass123",
        },
        format="json",
    )
    assert response.status_code == 200
    assert response.data["username"] == "updateduser"


@pytest.mark.django_db
def test_delete_user(authenticated_client, created_user):
    user_id = created_user.id
    response = authenticated_client.delete(f"/api/users/{user_id}/")
    assert response.status_code == 204
