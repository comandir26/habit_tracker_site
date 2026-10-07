"""Isolated database for API tests; production settings remain PostgreSQL."""
import os

os.environ.setdefault("SECRET_KEY", "test-only-secret-key")

from .settings import *  # noqa: F403,E402

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
