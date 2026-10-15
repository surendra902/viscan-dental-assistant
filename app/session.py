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
        modality: Optional[str] = None,
        clear_report_if_none: bool = False
    ):
        sess = self.get_or_create(session_id)
        if patient_id is not None:
            # If switching to a new patient, clear prior patient's report unless a new report is provided
            if sess.last_patient_id and sess.last_patient_id.lower() != patient_id.lower():
                if report_id is None:
                    sess.last_report_id = None
            sess.last_patient_id = patient_id
        if patient_name is not None:
            sess.last_patient_name = patient_name
        if report_id is not None:
            sess.last_report_id = report_id
        elif clear_report_if_none:
            sess.last_report_id = None
        if modality is not None:
            sess.last_modality = modality

    def add_message(self, session_id: str, role: str, content: str):
        sess = self.get_or_create(session_id)
        sess.history.append({"role": role, "content": content})
        if len(sess.history) > 20:
            sess.history = sess.history[-20:]

    def clear(self, session_id: str):
        if session_id in self._sessions:
            del self._sessions[session_id]

session_manager = SessionManager()
