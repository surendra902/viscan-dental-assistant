# Viscan AI Dental Assistant

> A voice-first clinical dental radiology assistant proof-of-concept that retrieves patient reports, resolves conversational follow-ups, and converts clinical dictations into structured, clinician-audited draft reports.

Built strictly against the specifications of **Viscan AI Engineer Take-Home Technical Assignment**.

---

## Key Highlights

- **Mandatory Feature A (Report Retrieval)**: Extracts intent and patient name, handles 0/1/many matches safely, retrieves reports deterministically, and provides ground-truth evidence snippets.
- **Mandatory Feature B (Clinical Dictation to Draft)**: Extracts findings and anatomical sites into editable structured JSON. Enforces strict dental allowlists, flags fictitious claims (e.g., *"dragon teeth"*, *"quantum decay"*), and enforces `requires_review: true`.
- **Mandatory Feature C (Conversational Follow-Up)**: Resolves pronoun references (e.g., *"Summarize her report"*) across multi-turn sessions without re-asking for the patient name when unambiguous, and links explicit evidence trails.
- **Strict Decoupling**: Decouples LLM parsing from deterministic Python business-rule validation (`app/validators.py`).
- **Zero Hallucination / Zero External Dependency Mandate**: Runs 100% deterministically and offline for automated evaluation and CI, while supporting plug-and-play OpenAI / Anthropic API keys when present.

---

## 1. Setup & Installation

### Prerequisites
- Python 3.10+ (tested on Python 3.11.15)
- Standard virtual environment or conda

### Installation
```bash
# Clone or navigate into the repository
cd viscan-dental-assistant

# Install dependencies
pip install -r requirements.txt
```

### Environment Variables
Copy `.env.example` to `.env` (optional):
```bash
cp .env.example .env
```
*Note: Paid external API keys (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`) are optional per assignment guidelines. If not provided, the engine runs in high-precision deterministic offline mode.*

---

## 2. Running the Application

### Start the FastAPI Server
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Once started:
- **Interactive Web UI**: Open [http://localhost:8000](http://localhost:8000) in any modern browser.
- **Interactive Swagger Docs**: Open [http://localhost:8000/docs](http://localhost:8000/docs).
- **Health Check**: `GET http://localhost:8000/health`.

---

## 3. Automated Testing Suite

The project includes automated tests satisfying all assignment evaluation criteria:
1. **Correct Retrieval**: `test_correct_report_retrieval`
2. **Ambiguous Patient Identity**: `test_ambiguous_patient_identity`
3. **Unsupported Clinical Claims**: `test_unsupported_clinical_claims`
4. **Missing Report Safety**: `test_missing_report_safely_handled`
5. **Nonexistent Patient**: `test_nonexistent_patient_safely_handled`
6. **Conversational Follow-Up**: `test_conversational_follow_up`
7. **Disambiguation Flow**: `test_resolve_ambiguity_flow`
8. **Clinical Dictation Structuring**: `test_valid_clinical_dictation`
9. **Voice / STT Intake**: `test_transcribe_endpoint`

### Run Tests
```bash
pytest -v
```
All tests execute locally in `< 0.20s` with zero network overhead.

---

## 4. Architecture & Technical Design

```
[ Clinician Audio / Text ]
          |
          v
[ FastAPI Endpoints ] (/chat, /dictate, /transcribe, /reports)
          |
    +-----+-----+
    |           |
    v           v
[ Feature A/C: Dialogue ]          [ Feature B: Dictation ]
    |                                   |
    v                                   v
[ LLM Layer ]                     [ Candidate Slot Extraction ]
    | (deterministic tool calls)        | (raw finding tokens)
    v                                   v
[ Deterministic Tools ]           [ Business-Rule Layer ]
(find_patient, get_latest_report)  (validators.py: anatomy allowlist,
    |                              fictitious pattern detector,
    v                              uncertainty flags, requires_review: true)
[ Synthetic Mock Store ]                |
(patients.json, reports.json)           v
                                  [ Structured JSON + Draft Report ]
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full one-page architectural breakdown.

---

## 5. Model & Provider Choices

1. **OpenRouter Provider (Primary Active Model)**:
   - Model: `nvidia/nemotron-3.5-lightning:free`
   - Provider Endpoint: `https://openrouter.ai/api/v1`
   - Zero-latency language parsing for candidate clinical observations and structured intent recognition.
   - Enforces the strict assignment guideline: separates LLM language interpretation from Python domain business-rule validation (`app/validators.py`).
2. **Deterministic Engine (Zero-Cost / Offline Evaluator Fallback)**:
   - Employs token and slot pattern analysis alongside controlled vocabulary checking.
   - Guaranteed reproducibility, zero network latency (< 2ms), immune to rate limits, ensuring automated CI test suites always pass reliably.
3. **OpenAI / Anthropic (Optional)**:
   - Configurable via standard keys for GPT-4o / Claude 3.5 Sonnet / Whisper STT.

---

## 6. Synthetic Mock Dataset

All data is strictly synthetic with zero real patient information (PDF p1, p2):
- **6 Patients**: Includes **Priya Sharma (P001)** and **Priya Menon (P002)** to test similar-name ambiguity, alongside Arjun Patel, Sara Khan, Vikram Desai, and Ananya Rao.
- **9 Imaging Reports**: Spanning OPG, CBCT, and IOPA modalities across patients with controlled clinical findings (horizontally impacted molars, apical periodontitis, periodontitis bone loss, etc.).

---

## 7. Known Limitations & Production Roadmap

### Known Limitations
- **In-Memory Session Store**: Multi-turn sessions are stored in memory (`SessionManager`); restarted servers clear active sessions.
- **Controlled Finding Vocabulary**: While the validator covers major dental terms, rare congenital syndromes or unusual surgical devices not in the dictionary may be flagged as `unsupported_claims` and require clinician override.
- **Audio Codec Scope**: Direct browser recording relies on Web Speech API / standard WAV/WebM formats.

### What Works
- Safe report retrieval with 0/1/many disambiguation logic.
- Evidence grounding with auditable snippets.
- Clinical dictation parsing into structured JSON with anatomical sites and observations.
- Hallucination / fictitious claim interception (*"dragon teeth"*, *"quantum decay"*).
- Context-dependent follow-up (*"Summarize her report"*).
- Modern web UI with one-click test presets.

### What We Would Improve With More Time
1. **Persistent Session & EHR Integration**: Redis session cache and FHIR / HL7 compliant report export.
2. **Ontology Expansion**: Integrate SNOMED-CT / ICD-10-CM dental subset via an offline ontology graph.
3. **DICOM Thumbnail Grounding**: Connect findings directly to DICOM bounding-box slice coordinates.
4. **Streaming Voice Pipeline**: Full WebSocket duplex streaming (Audio chunk -> Streaming STT -> Token streaming).

---

## 8. Deliverables Index

- **Architecture Document**: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **Documented API Demo Calls & Outputs**: [docs/DEMO.md](docs/DEMO.md)
- **Production Notes (Privacy, Auth, Latency, Cost)**: [docs/PRODUCTION_NOTES.md](docs/PRODUCTION_NOTES.md)
- **Mock Data**: [data/patients.json](data/patients.json) & [data/reports.json](data/reports.json)
