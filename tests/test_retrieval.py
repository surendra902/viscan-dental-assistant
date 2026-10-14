import pytest
from fastapi.testclient import TestClient

def test_correct_report_retrieval(client: TestClient):
    """
    Test 1 (Required by PDF p2 s3): Correct retrieval.
    Given: 'Open Priya Sharma's latest OPG report'
    Must: Extract intent & patient name, query mock data, return correct report (R101),
          and include source report / evidence.
    """
    response = client.post("/chat", json={
        "message": "Open Priya Sharma's latest OPG report",
        "session_id": "test-session-retrieval"
    })

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "success"
    assert data["intent"] == "retrieve_report"
    assert data["patient"] is not None
    assert data["patient"]["patient_id"] == "P001"
    assert data["patient"]["name"] == "Priya Sharma"

    # Verify latest OPG is returned (R101 from 2026-01-15, not older R102 from 2025-06-10)
    assert data["report"] is not None
    assert data["report"]["report_id"] == "R101"
    assert data["report"]["modality"] == "OPG"
    assert "2026-01-15" in data["report"]["date"]

    # Verify evidence is provided (PDF requirement)
    assert data["evidence"] is not None
    assert data["evidence"]["report_id"] == "R101"
    assert "horizontally impacted" in data["response_text"].lower()

def test_missing_report_safely_handled(client: TestClient):
    """
    Edge case required by PDF p1 s1A: 'Handle missing reports safely'.
    Sara Khan (P004) has an IOPA report, but no CBCT report.
    """
    response = client.post("/chat", json={
        "message": "Open Sara Khan's latest CBCT report",
        "session_id": "test-session-missing"
    })

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "not_found"
    assert "no cbct report was found" in data["response_text"].lower()

def test_nonexistent_patient_safely_handled(client: TestClient):
    """
    Edge case: Non-existent patient.
    """
    response = client.post("/chat", json={
        "message": "Open John Doe's latest OPG report",
        "session_id": "test-session-notfound"
    })

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "not_found"
    assert "not found in records" in data["response_text"].lower()

def test_conversational_follow_up(client: TestClient):
    """
    Feature C (Mandatory, PDF p1 s1C):
    Support one context-dependent follow-up e.g. 'Summarize her report'
    without asking for the patient again when the reference is unambiguous.
    Show the source report or evidence used for each answer.
    """
    session_id = "test-session-followup"

    # Turn 1: Retrieve report
    r1 = client.post("/chat", json={
        "message": "Open Priya Sharma's latest OPG report",
        "session_id": session_id
    })
    assert r1.status_code == 200
    assert r1.json()["status"] == "success"

    # Turn 2: Follow-up pronoun reference
    r2 = client.post("/chat", json={
        "message": "Summarize her report",
        "session_id": session_id
    })

    assert r2.status_code == 200
    data2 = r2.json()
    assert data2["status"] == "success"
    assert data2["intent"] == "follow_up_summary"
    assert data2["patient"]["name"] == "Priya Sharma"
    assert data2["report"]["report_id"] == "R101"
    assert data2["evidence"] is not None
    assert "Summary for Priya Sharma" in data2["response_text"]
