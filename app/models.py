from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field

class Patient(BaseModel):
    patient_id: str
    name: str
    date_of_birth: str
    gender: str
    contact: str

class Report(BaseModel):
    report_id: str
    patient_id: str
    modality: str
    date: str
    referring_doctor: str
    clinical_indication: str
    findings: List[str]
    impression: str
    evidence_snippet: str

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Clinical query or retrieval command")
    session_id: str = Field(default="default-session", description="Session ID for multi-turn context tracking")

class ChatResponse(BaseModel):
    session_id: str
    intent: str
    response_text: str
    status: str = "success"  # "success", "ambiguous", "not_found", "error"
    patient: Optional[Patient] = None
    report: Optional[Report] = None
    candidates: Optional[List[Patient]] = None
    evidence: Optional[Dict[str, Any]] = None
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list)

class DictateRequest(BaseModel):
    transcript: str = Field(..., min_length=1, description="Dictated observation transcript")
    session_id: Optional[str] = Field(default="default-session", description="Session context")
    patient_id: Optional[str] = None

class StructuredFinding(BaseModel):
    anatomical_site: str
    observation: str
    confidence: float
    is_supported: bool

class DictateResponse(BaseModel):
    session_id: str
    transcript: str
    structured_findings: List[StructuredFinding]
    draft_report: str
    uncertainties: List[str]
    unsupported_claims: List[str]
    requires_review: bool = True

class TranscribeResponse(BaseModel):
    transcript: str
    source: str
