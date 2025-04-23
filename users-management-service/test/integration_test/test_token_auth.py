import pytest  # type: ignore
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_token_auth_flow(created_user):
    client = APIClient()

    # Login
    login_resp = client.post(
        "/api/api-token-auth/",
        {"username": created_user.username, "password": "testpass123"},
    )
    assert login_resp.status_code == 200
    token = login_resp.data["token"]

    # Access protected endpoint
    client.credentials(HTTP_AUTHORIZATION=f"Token {token}")
    protected_resp = client.get("/api/user-info/")
    assert protected_resp.status_code == 200
