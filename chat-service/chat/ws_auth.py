# chat/ws_auth.py

from urllib.parse import parse_qs
from channels.db import database_sync_to_async
import requests
import logging

logger = logging.getLogger(__name__)


class SimpleUser:
    def __init__(self, id=None, username="anonymous", email=None):
        self.id = id
        self.username = username
        self.email = email

    @property
    def is_authenticated(self):
        return self.id is not None


@database_sync_to_async
def get_user_from_token(token_key):
    try:
        headers = {"Authorization": f"Token {token_key}"}
        valid_resp = requests.get(
            "http://users-management-service:8001/api/validate-token/", headers=headers
        )
        if valid_resp.status_code == 200 and valid_resp.json().get("valid"):
            user_resp = requests.get(
                "http://users-management-service:8001/api/user-info/", headers=headers
            )
            if user_resp.status_code == 200:
                data = user_resp.json()
                return SimpleUser(
                    id=data["id"], username=data["username"], email=data["email"]
                )
    except Exception as e:
        logger.warning(f"[TokenAuthMiddlewareStack] Token verification failed: {e}")
    return SimpleUser()


def TokenAuthMiddlewareStack(inner):
    async def middleware(scope, receive, send):
        query_string = scope.get("query_string", b"").decode()
        params = parse_qs(query_string)
        token = params.get("token", [None])[0]

        user = await get_user_from_token(token)
        scope["user"] = user

        logger.warning(
            f"[TokenAuthMiddlewareStack] Token: {token} → user: {user.username}, is_authenticated: {user.is_authenticated}"
        )

        return await inner(scope, receive, send)

    return middleware
