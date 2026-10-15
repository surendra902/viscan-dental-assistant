"""New coverage: spell typo guard, bulk guardrail, contextual memory (RAG)."""
from fastapi.testclient import TestClient
from app.main import app
from app.session import session_manager
from app.llm import llm_engine

def _client():
    llm_engine.client = None
    return TestClient(app)

def test_spell_typo_does_not_hallucinate():
    """Arjun Patil (typo) must NOT silently return Arjun Patel -> must 404 with suggestion."""
    c = _client()
    sid = "spell-pat"
    session_manager._sessions.pop(sid, None)
    r = c.post("/chat", json={"message": "Open Arjun Patil's latest OPG report", "session_id": sid})
    d = r.json()
    assert d["status"] == "not_found", d["response_text"][:200]
    assert "Arjun Patel" in d["response_text"]  # did-you-mean
    assert d["patient"] is None

def test_spell_typo_priya_sharna_suggests():
    c = _client()
    sid = "spell-priya"
    session_manager._sessions.pop(sid, None)
    r = c.post("/chat", json={"message": "Open Priya Sharna's latest OPG report", "session_id": sid})
    d = r.json()
    # "Priya Sharna" hits ambiguous Priya path (returns multiple candidates), or not_found with hint.
    # Both are guardrailed (not hallucinated as a different patient).
    assert "Priya Sharma" not in str(d.get("patient") or "") or d["status"] in ("ambiguous", "not_found")

def test_bulk_guardrail_blocks_all_patients():
    c = _client()
    for msg in ["show all patients", "show all data of patients", "list all patients", "give all patient data"]:
        sid = f"bulk-{msg[:6]}"
        session_manager._sessions.pop(sid, None)
        r = c.post("/chat", json={"message": msg, "session_id": sid})
        d = r.json()
        assert d["status"] == "guardrail_blocked", f"bulk '{msg}' not blocked: {d}"
        assert "can't share all" in d["response_text"].lower()

def test_modality_followup_via_context_memory():
    """RAG context memory: after OPG, 'what about her CBCT?' must resolve via last_patient_id."""
    c = _client()
    sid = "mem-cbct"
    session_manager._sessions.pop(sid, None)
    r1 = c.post("/chat", json={"message": "Open Priya Sharma's latest OPG report", "session_id": sid})
    assert r1.json()["status"] == "success"
    r2 = c.post("/chat", json={"message": "what about her CBCT?", "session_id": sid})
    d2 = r2.json()
    assert d2["status"] == "success", d2["response_text"][:300]
    assert d2["report"]["modality"] == "CBCT"
    assert d2["patient"]["patient_id"] == "P001"

def test_exact_name_still_resolves():
    c = _client()
    sid = "exact-ok"
    session_manager._sessions.pop(sid, None)
    r = c.post("/chat", json={"message": "Open Arjun Patel's latest OPG report", "session_id": sid})
    assert r.json()["status"] == "success"
    assert r.json()["patient"]["patient_id"] == "P003"
