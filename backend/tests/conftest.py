"""
Shared pytest fixtures.

Key design point: `settings` (app.config) and the embedding provider cache
(app.services.embeddings._provider_instance) are both module-level
singletons. Tests mutate them via monkeypatch so each test gets an isolated
SQLite file and a fresh provider cache, and everything is restored
automatically when the test ends.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings  # noqa: E402
from app.database import init_db  # noqa: E402
from app.services import embeddings as embeddings_module  # noqa: E402


@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    """Point the app at a fresh, isolated SQLite file for this test."""
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(settings, "database_path", str(db_path))
    monkeypatch.setattr(settings, "embedding_provider", "local")
    monkeypatch.setattr(settings, "generation_provider", "openai")
    monkeypatch.setattr(settings, "openai_api_key", None)

    # Reset the cached embedding provider singleton so it's rebuilt against
    # the new settings rather than reused from a previous test.
    monkeypatch.setattr(embeddings_module, "_provider_instance", None)

    init_db()
    yield db_path


@pytest.fixture
def client(temp_db):
    from fastapi.testclient import TestClient
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client
