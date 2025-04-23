import pytest  # type: ignore
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_login_token_auth(created_user):
    client = APIClient()
    response = client.post(
        "/api/api-token-auth/",
        {"username": created_user.username, "password": "testpass123"},
    )
    assert response.status_code == 200
    assert "token" in response.data
