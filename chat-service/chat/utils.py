import requests
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
import logging
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)


def get_user_model_instance():
    return get_user_model()


def validate_token(token):
    url = f"{settings.USERS_SERVICE_URL}/api/validate-token/"
    headers = {"Authorization": f"Token {token}"}
    logger.debug(f"Sending token validation request to {url} with headers {headers}")
    response = requests.get(url, headers=headers)
    logger.debug(f"Token validation response: {response.status_code} - {response.text}")
    if response.status_code != 200:
        return False
    try:
        return response.json().get("valid", False)
    except ValueError as e:
        logger.error(f"Error parsing token validation response: {e}")
        return False


def get_user_info(token):
    url = f"{settings.USERS_SERVICE_URL}/api/user-info/"
    headers = {"Authorization": f"Token {token}"}
    logger.debug(f"Sending user info request to {url} with headers {headers}")
    response = requests.get(url, headers=headers)
    logger.debug(f"User info response: {response.status_code} - {response.text}")
    if response.status_code != 200:
        return None
    try:
        return response.json()
    except ValueError as e:
        logger.error(f"Error parsing user info response: {e}")
        return None


class CustomTokenAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Token "):
            return None

        token = auth_header.split(" ")[1]
        logger.debug(f"Authenticating token: {token}")

        if not validate_token(token):
            logger.debug("Token validation failed")
            raise AuthenticationFailed("Invalid token.")

        user_info = get_user_info(token)
        if not user_info:
            logger.debug("User info not found")
            raise AuthenticationFailed("User info not found.")

        User = get_user_model_instance()
        user, created = User.objects.get_or_create(
            id=user_info["id"],
            defaults={"username": user_info["username"], "email": user_info["email"]},
        )
        if not created:
            user.username = user_info["username"]
            user.email = user_info["email"]
            user.save()

        logger.debug(f"Authenticated user: {user_info}")
        return (user, token)
