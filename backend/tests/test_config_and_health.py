"""
Tests for the two small, cheap architecture improvements kept after
simplifying back down: fail-fast config validation and a DB-aware health
check. (A ContextVar-based request-id-everywhere logging mechanism and a
repository layer were tried and then deliberately reverted -- good patterns
in the abstract, but more machinery than this app's actual debuggability
and persistence needs justify. See README.)
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def test_invalid_embedding_provider_value_fails_fast(monkeypatch):
    """A typo like EMBEDDING_PROVIDER=OpenAI (wrong case) must raise a clear
    error at startup, not silently behave like "local"."""
    from pydantic import ValidationError

    from app.config import Settings

    monkeypatch.setenv("EMBEDDING_PROVIDER", "OpenAI")
    with pytest.raises(ValidationError):
        Settings()


def test_invalid_generation_provider_value_fails_fast(monkeypatch):
    from pydantic import ValidationError

    from app.config import Settings

    monkeypatch.setenv("GENERATION_PROVIDER", "anthropic")
    with pytest.raises(ValidationError):
        Settings()


def test_valid_provider_values_construct_cleanly(monkeypatch):
    from app.config import Settings

    monkeypatch.setenv("EMBEDDING_PROVIDER", "openai")
    monkeypatch.setenv("GENERATION_PROVIDER", "extractive")
    s = Settings()
    assert s.embedding_provider == "openai"
    assert s.generation_provider == "extractive"


def test_health_check_reports_database_status(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["database"] == "ok"
    assert body["status"] == "ok"
