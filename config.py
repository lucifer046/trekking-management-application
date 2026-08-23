"""
Application configuration.

Reads settings from environment variables (loaded from a local .env file in
development via python-dotenv) instead of the hardcoded SECRET_KEY / DB URI
/ debug=True that the original prototype used. See .env.example for the
full list of variables a deployment can override.
"""
import os
from datetime import timedelta

from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Load .env if present. Safe to call even when the file doesn't exist (e.g.
# in CI or production where real env vars are injected directly).
load_dotenv(os.path.join(BASE_DIR, ".env"))


def _bool_env(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


class Config:
    """Shared defaults. Never used directly — pick a subclass below."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-insecure-secret-key-change-me")

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"connect_args": {"timeout": 15}}

    # Session / cookie hardening (safe defaults for both dev and prod).
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = timedelta(days=14)
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None  # tokens don't expire mid-session

    # Trek image uploads.
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB hard cap, enforced by Flask itself
    UPLOAD_ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
    UPLOAD_MAX_IMAGES_PER_TREK = 6

    RATELIMIT_ENABLED = True
    RATELIMIT_STORAGE_URI = "memory://"

    # Seed / bootstrap admin account (used by `flask create-admin` and seed.py).
    ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@trekking.com")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "Admin@12345")
    ADMIN_NAME = os.environ.get("ADMIN_NAME", "Platform Admin")

    ITEMS_PER_PAGE = 12
    ADMIN_ROWS_PER_PAGE = 15


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///" + os.path.join(BASE_DIR, "instance", "trekking.db")
    )


class TestingConfig(Config):
    TESTING = True
    DEBUG = False
    WTF_CSRF_ENABLED = False  # tests post form data directly without a live CSRF token
    RATELIMIT_ENABLED = False
    SQLALCHEMY_DATABASE_URI = os.environ.get("TEST_DATABASE_URL", "sqlite://")
    ADMIN_PASSWORD = "Admin@12345"


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///" + os.path.join(BASE_DIR, "instance", "trekking.db")
    )


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
