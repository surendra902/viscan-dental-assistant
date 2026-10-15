import pytest
from starlette.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_spaced_patient_id_direct_lookup(client: TestClient):
    """Voice transcript 'P 006' directly identifies patient P006."""
    resp = client.post("/chat", json={
        "message": "P 006",
        "session_id": "test-pid-1"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["patient"]["patient_id"] == "P006"
    assert "Ananya Rao" in data["response_text"]

def test_prefixed_patient_id_lookup(client: TestClient):
    """Voice transcript 'patient ID P 006' directly identifies patient P006."""
    resp = client.post("/chat", json={
        "message": "patient ID P 006",
        "session_id": "test-pid-2"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["patient"]["patient_id"] == "P006"
    assert "Ananya Rao" in data["response_text"]

def test_open_latest_report_of_id(client: TestClient):
    """Voice transcript 'open latest report of ID P 006' retrieves report."""
    resp = client.post("/chat", json={
        "message": "open latest report of ID P 006",
        "session_id": "test-pid-3"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["report"]["patient_id"] == "P006"
    assert "Retrieved OPG report for Ananya Rao" in data["response_text"]

def test_patient_name_identity_query(client: TestClient):
    """Voice transcript 'what is the patient name of PID p004' returns demographics."""
    resp = client.post("/chat", json={
        "message": "what is the patient name of PID p004",
        "session_id": "test-pid-4"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["intent"] == "patient_identity"
    assert data["patient"]["patient_id"] == "P004"
    assert "Sara Khan" in data["response_text"]
