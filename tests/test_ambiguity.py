import pytest
from fastapi.testclient import TestClient

def test_ambiguous_patient_identity(client: TestClient):
    """
    Test 2 (Required by PDF p2 s3): Ambiguous patient identity.
    Given: 'Open Priya's latest OPG report'
    Must: Identify that multiple patients match ('Priya Sharma' and 'Priya Menon'),
          ask for disambiguation, and NOT guess or arbitrarily pick one.
    """
    response = client.post("/chat", json={
        "message": "Open Priya's latest OPG report",
        "session_id": "test-session-ambiguity"
    })

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "ambiguous"
    assert data["intent"] == "retrieve_report"
    assert data["report"] is None  # Must NOT return a report when identity is ambiguous!
    assert data["candidates"] is not None
    assert len(data["candidates"]) == 2

    candidate_ids = {c["patient_id"] for c in data["candidates"]}
    assert "P001" in candidate_ids
    assert "P002" in candidate_ids

    # Verify the response message clearly prompts the user
    assert "Multiple patients found" in data["response_text"]
    assert "Priya Sharma" in data["response_text"]
    assert "Priya Menon" in data["response_text"]

def test_resolve_ambiguity_flow(client: TestClient):
    """
    Follow-up test: Clinician clarifies the ambiguous patient name in the next turn.
    """
    session_id = "test-session-resolve"

    # Step 1: Ambiguous query
    r1 = client.post("/chat", json={
        "message": "Open Priya's latest OPG report",
        "session_id": session_id
    })
    assert r1.status_code == 200
    assert r1.json()["status"] == "ambiguous"

    # Step 2: Clinician disambiguates by providing full name
    r2 = client.post("/chat", json={
        "message": "Priya Sharma",
        "session_id": session_id
    })
    assert r2.status_code == 200
    data2 = r2.json()
    assert data2["status"] == "success"
    assert data2["patient"]["patient_id"] == "P001"
    assert data2["report"] is not None
