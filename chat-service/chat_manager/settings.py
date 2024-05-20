import os
from pathlib import Path
from dotenv import load_dotenv
import chat.utils
import chat.middleware

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("SECRET_KEY")

DEBUG = os.getenv("DEBUG", "False") == "True"

ALLOWED_HOSTS = [
    "*",
    "localhost",
    "127.0.0.1",
    "users-management-service",
    "chat-service",
    "*.users-management-service",  # Allow any port on users-management-service
    "*.chat-service",  # Allow any port on chat-service
]
print("ALLOWED_HOSTS:", os.environ.get("ALLOWED_HOSTS"))

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework.authtoken",
    "channels",
    "corsheaders",
    "channels_redis",
    "drf_spectacular",
    "chat",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.BrokenLinkEmailsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
MIDDLEWARE.insert(0, "chat.middleware.LogHeadersMiddleware")


ROOT_URLCONF = "chat_manager.urls"

CORS_ALLOW_ALL_ORIGINS = True

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "chat_manager.wsgi.application"
ASGI_APPLICATION = "chat_manager.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("CHAT_POSTGRES_DB"),
        "USER": os.getenv("CHAT_POSTGRES_USER"),
        "PASSWORD": os.getenv("CHAT_POSTGRES_PASSWORD"),
        "HOST": os.getenv("CHAT_POSTGRES_HOST"),
        "PORT": 5432,
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = "/static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ("chat.utils.CustomTokenAuthentication",),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("redis", 6379)],
        },
    },
}

USERS_SERVICE_URL = os.getenv("USERS_SERVICE_URL", "http://localhost:8001")

SPECTACULAR_SETTINGS = {
    "TITLE": "Chat Service API",
    "DESCRIPTION": "Real-time communication and chat room management API",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "DEBUG": True,
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "DEBUG",
    },
    "django": {
        "handlers": ["console"],
        "level": "INFO",
        "propagate": True,
    },
    "django.request": {
        "handlers": ["console"],
        "level": "DEBUG",
        "propagate": False,
    },
    "django.db.backends": {
        "handlers": ["console"],
        "level": "DEBUG",
        "propagate": False,
    },
}
