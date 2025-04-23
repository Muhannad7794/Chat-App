import pytest # type: ignore
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def created_user(db):
    return User.objects.create_user(
        username="testuser", password="testpass123", email="test@example.com"
    )


@pytest.fixture
def authenticated_client(created_user):
    client = APIClient()
    response = client.post(
        "/api/api-token-auth/", {"username": "testuser", "password": "testpass123"}
    )
    token = response.data["token"]
    client.credentials(HTTP_AUTHORIZATION=f"Token {token}")
    return client
