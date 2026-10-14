from fastapi.testclient import TestClient
from app.main import app
from app.session import session_manager
from app.llm import llm_engine

def test_explicit_patient_name_summary_sequence():
    session_manager._sessions.clear()
    client = TestClient(app)

    # 1. Open Arjun Patel's latest CBCT report
    r1 = client.post("/chat", json={"message": "Open Arjun Patel's latest CBCT report", "session_id": "test-c18"})
    assert r1.status_code == 200
    d1 = r1.json()
    assert d1["status"] == "success"
    assert d1["patient"]["patient_id"] == "P003"
    assert d1["report"]["report_id"] == "R106"

    # 2. Summarize his report
    r2 = client.post("/chat", json={"message": "Summarize his report", "session_id": "test-c18"})
    assert r2.status_code == 200
    d2 = r2.json()
    print("d2 response:", d2)
    assert d2["status"] == "success"
    assert d2["patient"]["patient_id"] == "P003"
    assert d2["report"]["report_id"] == "R106"
    assert "Summary for Arjun Patel" in d2["response_text"]

    # 3. Summarize Sara Khan's report (C18)
    r3 = client.post("/chat", json={"message": "Summarize Sara Khan's report", "session_id": "test-c18"})
    assert r3.status_code == 200
    d3 = r3.json()
    print("d3 response:", d3["response_text"])
    assert d3["status"] == "success"
    assert d3["patient"]["patient_id"] == "P004", f"Expected P004 but got {d3['patient']['patient_id']}"
    assert d3["report"]["patient_id"] == "P004"
    assert "Summary for Sara Khan" in d3["response_text"]
    assert "Arjun Patel" not in d3["response_text"]

if __name__ == "__main__":
    test_explicit_patient_name_summary_sequence()
    print("ALL TESTS PASSED!")
