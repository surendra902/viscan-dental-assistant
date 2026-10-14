from typing import Dict, Optional, List, Any
from pydantic import BaseModel, Field

class SessionState(BaseModel):
    session_id: str
    last_patient_id: Optional[str] = None
    last_patient_name: Optional[str] = None
    last_report_id: Optional[str] = None
    last_modality: Optional[str] = None
    history: List[Dict[str, Any]] = Field(default_factory=list)

class SessionManager:
    def __init__(self):
        self._sessions: Dict[str, SessionState] = {}

    def get_or_create(self, session_id: str) -> SessionState:
        if session_id not in self._sessions:
            self._sessions[session_id] = SessionState(session_id=session_id)
        return self._sessions[session_id]

    def update_context(
        self,
        session_id: str,
        patient_id: Optional[str] = None,
        patient_name: Optional[str] = None,
        report_id: Optional[str] = None,
        modality: Optional[str] = None
    ):
        sess = self.get_or_create(session_id)
        if patient_id:
            sess.last_patient_id = patient_id
        if patient_name:
            sess.last_patient_name = patient_name
        if report_id:
            sess.last_report_id = report_id
        if modality:
            sess.last_modality = modality

    def add_message(self, session_id: str, role: str, content: str):
        sess = self.get_or_create(session_id)
        sess.history.append({"role": role, "content": content})

    def clear(self, session_id: str):
        if session_id in self._sessions:
            del self._sessions[session_id]

session_manager = SessionManager()
