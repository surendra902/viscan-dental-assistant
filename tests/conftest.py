import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.data_store import data_store
from app.session import session_manager
from app.llm import llm_engine

@pytest.fixture(autouse=True)
def reset_sessions(monkeypatch):
    """Resets session manager, reloads data store, and ensures deterministic test runs."""
    session_manager._sessions.clear()
    data_store.reload()
    # Ensure automated tests run with deterministic offline engine (no network flakiness / rate-limits)
    monkeypatch.setattr(llm_engine, "client", None)
    yield
    session_manager._sessions.clear()

@pytest.fixture
def client():
    return TestClient(app)
