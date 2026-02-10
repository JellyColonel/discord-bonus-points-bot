"""Shared test fixtures."""

import os
import tempfile

import pytest


@pytest.fixture
def temp_db_path():
    """Create a temporary database file path."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    try:
        os.unlink(path)
    except OSError:
        pass


@pytest.fixture
def db(temp_db_path):
    """Create a Database instance with a temporary SQLite file."""
    from web.database import Database
    return Database(temp_db_path)


@pytest.fixture
def app(temp_db_path):
    """Create a Flask test app with a temporary database."""
    # Set required env vars before importing config
    os.environ.setdefault("SECRET_KEY", "test-secret-key")
    os.environ.setdefault("DISCORD_CLIENT_ID", "test-client-id")
    os.environ.setdefault("DISCORD_CLIENT_SECRET", "test-client-secret")
    os.environ.setdefault("DISCORD_REDIRECT_URI", "http://localhost:5000/callback")

    from web.app import app as flask_app
    from web.app import db as app_db

    # Override the DB path for tests
    app_db.db_path = temp_db_path
    app_db.init_db()

    flask_app.config["TESTING"] = True
    flask_app.config["WTF_CSRF_ENABLED"] = False

    yield flask_app


@pytest.fixture
def client(app):
    """Create a Flask test client."""
    return app.test_client()


@pytest.fixture
def auth_session(client):
    """Create an authenticated test session."""
    with client.session_transaction() as sess:
        sess["user"] = {
            "id": "123456789",
            "username": "TestUser",
            "discriminator": "0",
            "avatar": None,
        }
    return client
