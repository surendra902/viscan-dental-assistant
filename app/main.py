import os
from pathlib import Path
from typing import Optional, List
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.models import (
    ChatRequest, ChatResponse,
    DictateRequest, DictateResponse,
    TranscribeResponse, Patient, Report
)
from app.data_store import data_store
from app.session import session_manager
from app.llm import llm_engine
from app.validators import validate_clinical_dictation

BASE_DIR = Path(__file__).parent.parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(
    title="Viscan AI Dental Assistant",
    description="Voice-first dental clinical assistant proof-of-concept for report retrieval and clinical dictation.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files if directory exists
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
def read_root():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "Viscan AI Dental Assistant API is running. Visit /docs for OpenAPI specs."}

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "viscan-dental-assistant",
        "mock_patients_loaded": len(data_store.get_all_patients()),
        "mock_reports_loaded": len(data_store.get_all_reports())
    }

@app.get("/patients", response_model=List[Patient])
def get_patients():
    """Returns all mock patients (synthetic data)."""
    return data_store.get_all_patients()

@app.get("/reports/{patient_id}", response_model=List[Report])
def get_patient_reports(patient_id: str):
    """Retrieves all reports for a specific patient ID."""
    reports = [r for r in data_store.get_all_reports() if r.patient_id.lower() == patient_id.lower()]
    if not reports:
        patient = data_store.get_patient_by_id(patient_id)
        if not patient:
            raise HTTPException(status_code=404, detail=f"Patient '{patient_id}' not found.")
        return []
    return reports

@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    """
    Main conversational interface:
    Handles report retrieval (Feature A), ambiguity handling, and conversational follow-up (Feature C).
    """
    if not request.message.strip():
        raise HTTPException(status_code=422, detail="Message cannot be empty or whitespace.")

    session = session_manager.get_or_create(request.session_id)
    session_manager.add_message(request.session_id, "user", request.message)

    result = llm_engine.process_chat(request.message, session)

    response = ChatResponse(
        session_id=request.session_id,
        intent=result.get("intent", "general"),
        status=result.get("status", "success"),
        response_text=result.get("response_text", ""),
        patient=result.get("patient"),
        report=result.get("report"),
        candidates=result.get("candidates"),
        evidence=result.get("evidence"),
        tool_calls=result.get("tool_calls", [])
    )

    session_manager.add_message(request.session_id, "assistant", response.response_text)
    return response

@app.post("/dictate", response_model=DictateResponse)
def dictate_endpoint(request: DictateRequest):
    """
    Clinical dictation to draft report (Feature B):
    Separates LLM parsing from business-rule validation.
    Enforces 'Do not invent observations; label uncertainty and require clinician review'.
    """
    if not request.transcript.strip():
        raise HTTPException(status_code=422, detail="Transcript cannot be empty or whitespace.")

    session_id = request.session_id or "default-session"

    # 1. LLM layer interprets transcript and extracts candidate findings
    raw_findings = llm_engine.parse_dictation(request.transcript)

    # 2. Business-rule validation layer checks anatomy allowlist and flags unsupported claims
    structured_findings, uncertainties, unsupported_claims, draft_report = validate_clinical_dictation(
        raw_findings,
        request.transcript
    )

    return DictateResponse(
        session_id=session_id,
        transcript=request.transcript,
        structured_findings=structured_findings,
        draft_report=draft_report,
        uncertainties=uncertainties,
        unsupported_claims=unsupported_claims,
        requires_review=True
    )

@app.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_endpoint(
    audio: Optional[UploadFile] = File(None),
    transcript_fallback: Optional[str] = Form(None)
):
    """
    Voice/STT intake stub (per PDF p2 notes):
    Accepts audio upload or fallback text transcript.
    If OPENAI_API_KEY is present and audio is uploaded, can call Whisper API.
    Otherwise, returns deterministic clinical transcription to keep offline tests robust.
    """
    if transcript_fallback:
        return TranscribeResponse(
            transcript=transcript_fallback,
            source="typed_transcript"
        )

    if audio:
        # Check if OpenAI Whisper API can be used
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            try:
                import openai
                client = openai.OpenAI(api_key=openai_key)
                audio_bytes = await audio.read()
                transcription = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=(audio.filename, audio_bytes)
                )
                return TranscribeResponse(
                    transcript=transcription.text,
                    source="whisper_api"
                )
            except Exception:
                # Graceful fallback if API call fails
                pass

        # Deterministic mock STT audio transcription
        return TranscribeResponse(
            transcript="Lower right third molar is horizontally impacted",
            source="mock_stt_audio"
        )

    raise HTTPException(status_code=422, detail="Either audio file or transcript_fallback must be provided.")
