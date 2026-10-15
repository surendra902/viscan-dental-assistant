from fastapi.testclient import TestClient
from app.main import app
from app.session import session_manager
from app.llm import llm_engine

def _c(sid):
    llm_engine.client = None
    session_manager._sessions.pop(sid, None)
    return TestClient(app)

def test_temporal_pronoun_followup():
    sid="t-temporal"
    c=_c(sid)
    assert c.post("/chat", json={"message":"Priya Sharma latest report","session_id":sid}).json()["status"]=="success"
    r=c.post("/chat", json={"message":"when did she came to hospital","session_id":sid}).json()
    assert r["status"]=="success"
    assert "when did she came" not in r["response_text"].lower()
    assert "not found" not in r["response_text"].lower()
    assert r["evidence"] is not None
