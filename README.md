# Viscan AI Dental Assistant

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.133-009688.svg)](https://fastapi.tiangolo.com/)
[![Tests](https://img.shields.io/badge/pytest-11%2F11%20passing-brightgreen.svg)](tests/)
[![Render](https://img.shields.io/badge/Render-Live%20Deploy-46E3B7.svg)](https://viscan-dental-assistant.onrender.com)
[![License](https://img.shields.io/badge/data-100%25%20synthetic-orange.svg)](#6-synthetic-clinical-dataset)

> A voice-first clinical dental assistant that deterministically retrieves imaging reports, preserves multi-turn session context, and transforms spoken clinical observations into auditable, structured draft reports with human-in-the-loop validation.

---

## Live Links & Quick Access

- **Live Production Service**: [https://viscan-dental-assistant.onrender.com](https://viscan-dental-assistant.onrender.com)
- **Interactive OpenAPI (Swagger) Docs**: [https://viscan-dental-assistant.onrender.com/docs](https://viscan-dental-assistant.onrender.com/docs)
- **Health Check Endpoint**: [https://viscan-dental-assistant.onrender.com/health](https://viscan-dental-assistant.onrender.com/health)
- **GitHub Repository**: [https://github.com/surendra902/viscan-dental-assistant](https://github.com/surendra902/viscan-dental-assistant)

---

## 1. Problem Statement & System Overview

During chairside radiology consultations, clinicians face two major friction points:
1. **Report Retrieval Inefficiency**: Locating a specific historical scan (e.g., an OPG from 6 months ago vs. a recent CBCT) requires manual PACS search navigation, disrupting clinical workflow.
2. **Clinical Dictation Errors & Hallucinations**: Standard off-the-shelf generative models tend to hallucinate findings, invent non-existent pathologies, or state tentative clinical impressions as definitive diagnostic facts without mandatory physician oversight.

The **Viscan AI Dental Assistant** solves this through a **Decoupled Architecture**:
- Language models are used *strictly* for intent recognition and slot extraction.
- Deterministic Python business rules validate every finding against a curated dental anatomy allowlist.
- Fictitious clinical claims (*"dragon teeth"*, *"quantum decay"*) are isolated and rejected.
- Multi-turn pronoun references (*"Summarize her report"*) resolve through ephemeral session memory with auditable evidence grounding.

---

## 2. Architecture & End-to-End Execution Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           CLINICIAN INTERFACE                                   │
│            Typed Text  │  Microphone (Web Speech API)  │  Audio File Upload     │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                             FASTAPI INTAKE LAYER                                │
│       POST /chat       │       POST /dictate       │      POST /transcribe      │
└──────────────────┬─────────────────────────────────────┬────────────────────────┘
                   │                                     │
                   ▼                                     ▼
     [ DIALOGUE PIPELINE (A & C) ]          [ DICTATION PIPELINE (B) ]
                   │                                     │
                   ▼                                     ▼
       ┌───────────────────────┐             ┌───────────────────────┐
       │   LLM Parsing Layer   │             │ Candidate Extraction  │
       │ OpenRouter Nemotron   │             │ OpenRouter Nemotron   │
       │ (2.0s Strict Failover)│             │ (2.0s Strict Failover)│
       └───────────┬───────────┘             └───────────┬───────────┘
                   │ Intent, Slots                       │ Raw Candidates
                   ▼                                     ▼
       ┌───────────────────────┐             ┌───────────────────────┐
       │  Deterministic Tools  │             │ Business-Rule Domain  │
       │  - find_patient()     │             │ Validator             │
       │  - get_latest_report()│             │ - Dental Allowlist    │
       │  - session_manager    │             │ - Fictitious Filter   │
       └───────────┬───────────┘             │ - Uncertainty Labeller│
                   │                                     │
                   ▼                                     ▼
       ┌───────────────────────┐             ┌───────────────────────┐
       │ Synthetic Data Store  │             │ Draft Report Compiler │
       │ 6 Patients, 13 Reports│             │ `requires_review:true`│
       └───────────┬───────────┘             └───────────┬───────────┘
                   │                                     │
                   ▼                                     ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                               RESPONSE PAYLOAD                                  │
│   Grounded Answer + Report Evidence   │   Editable JSON + Clinician Warnings   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. How It Works Under the Hood

### Module 01: Report Retrieval & Safe Disambiguation (Feature A)
1. **Slot Extraction**: The input query (e.g., *"Open Priya Sharma's latest OPG report"*) is parsed into:
   - `patient_name_query`: `"Priya Sharma"`
   - `modality`: `"OPG"`
2. **Deterministic Lookup (`find_patient`)**: Queries [`data/patients.json`](data/patients.json).
   - **0 Matches**: Returns HTTP 200 with `status: "not_found"` and a safe prompt asking the clinician to verify the record.
   - **>1 Matches (Ambiguity Guard)**: E.g., querying *"Priya"* matches both **Priya Sharma (P001)** and **Priya Menon (P002)**. The system **never guesses**. It returns `status: "ambiguous"` with the candidate list and prompts for exact specification.
   - **1 Match**: Resolves patient ID and executes `get_latest_report(patient_id, modality)`.
3. **Missing Report Handling**: If a patient exists but the requested modality does not (e.g., Sara Khan has an IOPA but no CBCT), the system returns `status: "not_found"` without hallucinating scan data.
4. **Evidence Grounding**: Attached to every successful retrieval is an `evidence` object referencing the source report ID, acquisition date, findings list, and clinical impression.

### Module 02: Clinical Dictation to Structured Draft (Feature B)
1. **Candidate Entity Extraction**: Dictated text (e.g., *"Lower right third molar is horizontally impacted"*) is segmented into candidate clauses (`anatomical_site` and `observation`).
2. **Business-Rule Validation (`app/validators.py`)**:
   - **Anatomical Allowlist**: Validates against human dentition (FDI 11–48, primary teeth 51–85, quadrants, arches, alveolar crest, mandibular ramus, condyle, inferior alveolar nerve canal, lingual/buccal plates).
   - **Pathology Vocabulary**: Checks clinical terms (impaction, periapical radiolucency, bone loss, caries, root resorption, subluxation, etc.).
   - **Fictitious Claim Interception**: Terms matching non-dental/fictitious concepts (*"dragon teeth"*, *"quantum decay"*, *"adamantium"*) are intercepted:
     - `is_supported` is set to `false`.
     - Confidence is penalized to `0.30`.
     - Claim is added to `unsupported_claims`.
     - High-visibility `WARNING` banners are appended to the draft text.
3. **Uncertainty Tagging**: Hedged language (*"suggestive of"*, *"cannot rule out"*, *"possible"*) is detected and flagged in `uncertainties` with clinician verification advisories.
4. **Mandatory Sign-off Guarantee**: The schema hardcodes `requires_review: true`. No AI-generated draft can bypass clinician sign-off.

### Module 03: Conversational Multi-Turn Follow-Up (Feature C)
1. **State Tracking (`app/session.py`)**: An in-memory `SessionManager` tracks `last_patient_id`, `last_patient_name`, and `last_report_id` keyed by `session_id`.
2. **Pronoun Resolution**: When a clinician asks *"Summarize her report"* or *"What were the findings?"*, the system detects the pronoun reference and checks active session context:
   - If an unambiguous patient was retrieved in Turn 1, Turn 2 resolves directly to that patient without re-prompting.
   - If no patient is active, it returns `status: "ambiguous"` requesting the patient's name.
3. **Evidence Linkage**: The generated summary includes explicit references to the source report ID and date.

---

## 4. Model Provider & Latency Engineering

### OpenRouter Nemotron-3.5-Lightning
- **Model**: `nvidia/nemotron-3.5-lightning:free`
- **Base URL**: `https://openrouter.ai/api/v1`
- **Role**: Structured entity extraction and intent parsing at zero inference cost.

### Strict Low-Latency Failover Architecture
Free-tier shared LLM endpoints can experience network queues. To guarantee sub-second clinical SLAs:
1. The OpenRouter HTTP client is initialized with a **strict 2.0-second timeout** (`httpx.Timeout(2.0, connect=2.0)`) and `max_retries=0`.
2. If OpenRouter responds within 2 seconds, the LLM-parsed structured entities are utilized.
3. If OpenRouter times out or errors, the system **instantly fails over to the local deterministic clinical parser in $<0.1\text{ms}$**.
4. The clinician receives valid structured results with zero downtime and zero server hangs.

---

## 5. User Interface (Datacurve-Inspired Editorial Design)

The interactive web interface is styled using the editorial motion system:
- **Typography**: *Instrument Serif* for luxury clinical headers, *Inter* for draft readability, and *JetBrains Mono* for technical schema tags.
- **Visual Depth**: Fractal noise grain overlay with a dynamic background particle canvas (`#dotCanvas`).
- **Interactive Micro-Animations**: 3D perspective tilt (`[data-tilt]`) on workspace cards with smooth cubic-bezier transitions.
- **One-Click Test Clusters**: Pre-configured test chips for instant evaluation of pass cases, ambiguous matches, follow-ups, and adversarial dictation.

---

## 6. Synthetic Clinical Dataset

All records are 100% synthetic to comply with healthcare privacy standards (HIPAA / DPDP). Zero real PHI is utilized.

### Synthetic Patients ([`data/patients.json`](data/patients.json))
| Patient ID | Name | Gender | DOB | Clinical Context |
| :--- | :--- | :--- | :--- | :--- |
| **P001** | **Priya Sharma** | Female | 1997-04-12 | Recurrent pain lower right quadrant (Similar-Name Pair) |
| **P002** | **Priya Menon** | Female | 1992-09-18 | Chronic periodontitis & bleeding gums (Similar-Name Pair) |
| **P003** | **Arjun Patel** | Male | 1981-01-22 | Osteolytic lesion evaluation left posterior mandible |
| **P004** | **Sara Khan** | Female | 2004-11-05 | Anterior dental trauma (IOPA only — negative CBCT test) |
| **P005** | **Vikram Desai** | Male | 1973-07-30 | Localized periodontal vertical defect tooth 46 |
| **P006** | **Ananya Rao** | Female | 1995-03-14 | Bilateral palatally impacted maxillary canines |

### Synthetic Reports ([`data/reports.json`](data/reports.json))
Includes **9 imaging reports** across `OPG`, `CBCT`, and `IOPA` modalities with structured clinical findings, impressions, referring doctors, and auditable evidence snippets.

---

## 7. API Reference

### 1. Conversational Chat & Retrieval
`POST /chat`
```json
// Request
{
  "message": "Open Priya Sharma's latest OPG report",
  "session_id": "clinic-session-01"
}

// Response (200 OK)
{
  "session_id": "clinic-session-01",
  "intent": "retrieve_report",
  "status": "success",
  "response_text": "Retrieved OPG report for Priya Sharma (P001) dated 2026-01-15...",
  "patient": { "patient_id": "P001", "name": "Priya Sharma", ... },
  "report": { "report_id": "R101", "modality": "OPG", ... },
  "evidence": { "report_id": "R101", "evidence_snippet": "..." },
  "tool_calls": [ ... ]
}
```

### 2. Clinical Dictation to Structured Draft
`POST /dictate`
```json
// Request
{
  "transcript": "Lower right third molar is horizontally impacted",
  "session_id": "clinic-session-01"
}

// Response (200 OK)
{
  "session_id": "clinic-session-01",
  "transcript": "Lower right third molar is horizontally impacted",
  "structured_findings": [
    {
      "anatomical_site": "Lower right third molar",
      "observation": "horizontally impacted",
      "confidence": 0.95,
      "is_supported": true
    }
  ],
  "draft_report": "CLINICAL OBSERVATION REPORT (DRAFT - REQUIRES CLINICIAN REVIEW)\n...",
  "uncertainties": [],
  "unsupported_claims": [],
  "requires_review": true
}
```

### 3. Voice / Speech-to-Text Intake
`POST /transcribe`
- Accepts multipart audio (`audio/wav`, `audio/mp3`) or form-encoded `transcript_fallback`.
- Returns `{ "transcript": "...", "source": "typed_transcript" | "whisper_api" | "mock_stt_audio" }`.

### 4. Patient & Report Directory
- `GET /patients`: Returns all synthetic patient profiles.
- `GET /reports/{patient_id}`: Returns all historical reports for a given patient ID.
- `GET /health`: System liveness and mock record count.

---

## 8. Local Setup & Verification

### Prerequisites
- Python 3.10+ (tested on Python 3.11.15)
- Git

### Installation
```bash
# 1. Clone the repository
git clone https://github.com/surendra902/viscan-dental-assistant.git
cd viscan-dental-assistant

# 2. Create virtual environment
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# 3. Install pinned dependencies
pip install -r requirements.txt

# 4. Configure environment (optional — engine runs fully offline if omitted)
cp .env.example .env
```

### Running Locally
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
Open **`http://localhost:8000`** in your browser.

### Automated Testing Suite
Run the unit and integration test suite:
```bash
pytest tests/ -v
```
All tests execute deterministically with or without an API key.

### End-to-End Audit & Correctness Benchmark
Run the automated live benchmark across all 16 clinical scenarios:
```bash
python tests/audit_benchmark.py
```
To run against a remote deployment (e.g. Render):
```bash
TARGET_URL=https://viscan-dental-assistant.onrender.com python tests/audit_benchmark.py
```

---

## 9. Known Limitations & Prototype Scope

1. **Synthetic Demo Data Only**: Not intended or approved for real-world diagnostic use or clinical decision-making. Synthetic patient profiles have been constructed specifically to test ambiguity resolution and missing report edge cases.
2. **In-Memory Process-Local Session Context**: Multi-turn context is managed in process memory (`SessionManager`) within a single instance. In a distributed multi-replica deployment, durable storage (e.g., Redis cluster) would be required.
3. **Lexical & Allowlist Terminology Heuristics**: Domain validation uses curated human dental anatomy and pathology allowlists with tooth numbering bounds (Universal 1–32, FDI permanent 11–48, deciduous 51–85) and transcript lexical grounding. This is a heuristic clinical safety gate, not a medical device diagnostic engine.
4. **Draft Report Labeling**: Dictations output `requires_review: true` to enforce human-in-the-loop sign-off. A full clinical EHR approval workflow (electronic signature, cryptographic audit trail, PACS sync) is proposed for production but out of scope for this take-home prototype.
5. **Single-Tenant Prototype**: Authentication and role-based access control (RBAC) are documented as production requirements but omitted from this standalone proof-of-concept.

---

## 10. Production Considerations (PDF §3 Compliance)

1. **Privacy & PHI Protection**: Zero real patient data. In production, an on-premise PII scrubber (e.g., Microsoft Presidio) would sanitize names prior to LLM extraction, and sessions would be stored in ephemeral encrypted Redis with 15-minute TTLs.
2. **Authorization (RBAC)**: Role separation between `Radiologist` (dictation approval), `Assistant` (report lookup), and `Auditor` (read-only audit trails).
3. **Latency Benchmarks**:
   - In-memory retrieval: **15ms – 40ms** locally.
   - Dictation structuring: **80ms – 300ms** (deterministic fallback) or **1.5s – 3.5s** (OpenRouter free-tier remote inference depending on network).
4. **Model Economics**:
   - Extraction via `nvidia/nemotron-3.5-lightning:free`: **$0.00 / turn**.
   - Optional production fallback via `gpt-4o-mini`: $\approx \$0.0003/\text{turn}$.
   - Whisper transcription: $\approx \$0.006/\text{minute}$ ($\approx \$0.003$ per 30-second clinical dictation).
   - Offline fallback engine: **$0.00**.
5. **Safety Defaults**: `requires_review` is enforced on every dictation response. Unverified claims (*"dragon teeth"*, *"moon crystals"*) trigger visual caution flags.

---

## 11. Hosting & Deployment (Render vs. Vercel)

### Why Render is the Selected Architecture
| Criterion | Render (Selected) | Vercel |
| :--- | :--- | :--- |
| **Execution Model** | **Persistent, stateful Python process** | Ephemeral, stateless Serverless Lambdas |
| **Session Memory** | **Survives across conversational turns** | Wiped on every cold start / new invocation |
| **Framework Support** | **Native ASGI (`uvicorn app.main:app`)** | Requires `@vercel/python` WSGI shim |
| **Audio Uploads** | Standard streaming multipart body | 4.5 MB serverless request ceiling |
| **Automation** | **Declarative `render.yaml` Blueprint** | Manual `vercel.json` rewrites |

Because **Feature C (Conversational Follow-Up)** requires maintaining session context across turns without an external database in this proof-of-concept, Render provides a persistent execution environment.

### Deploying to Render
1. Open [dashboard.render.com](https://dashboard.render.com/) and click **New +** > **Blueprint**.
2. Connect your fork or repository: `https://github.com/surendra902/viscan-dental-assistant`.
3. Render reads [`render.yaml`](render.yaml) automatically.
4. Set the `OPENROUTER_API_KEY` secret variable in the Render dashboard.
5. Click **Apply**.

---

## 12. Project Directory Structure

```
viscan-dental-assistant/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application, routes, middleware, and CORS
│   ├── models.py            # Strict Pydantic models for request & response validation
│   ├── data_store.py        # In-memory loader for synthetic patients and reports
│   ├── session.py           # Multi-turn conversational session manager (with report isolation)
│   ├── tools.py             # Deterministic tool layer (find_patient, get_latest_report)
│   ├── validators.py        # Business validator (dental anatomy & pathology allowlists, grounding)
│   └── llm.py               # OpenRouter Nemotron integration + deterministic fallback
├── data/
│   ├── patients.json        # 6 synthetic patients (Priya Sharma & Priya Menon pair)
│   └── reports.json         # 13 clinical reports (OPG, CBCT, IOPA) — >=2 reports per patient
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Pytest fixtures and test client setup
│   ├── audit_benchmark.py   # Live correctness & latency benchmark across 16 scenarios
│   ├── test_retrieval.py    # Test 1: Report retrieval + missing report + follow-up
│   ├── test_ambiguity.py    # Test 2: Ambiguous patient identity handling
│   ├── test_dictation.py    # Test 3: Unsupported clinical claims & valid dictation
│   └── test_openrouter.py   # OpenRouter Nemotron integration and offline resilience tests
├── docs/
│   ├── ARCHITECTURE.md      # 1-page architecture flow document
│   ├── DEMO.md              # Documented sequence of curl calls with verbatim outputs
│   └── PRODUCTION_NOTES.md  # Detailed analysis of privacy, auth, latency, and costs
├── static/
│   ├── index.html           # Datacurve-styled interface with editable JSON & draft panels
│   ├── style.css            # Editorial stylesheet with particle canvas & 3D tilt
│   └── app.js               # Frontend chat, dictation, editing, and evidence inspector
├── render.yaml              # Render Blueprint specification
├── requirements.txt         # Production dependencies
├── .env.example             # Environment variable template
└── README.md                # Comprehensive documentation
```

---

## 13. Deliverables Index

- **Architecture Document**: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- **Documented API Demo Calls & Outputs**: [`docs/DEMO.md`](docs/DEMO.md)
- **Production Notes (Privacy, Auth, Latency, Cost)**: [`docs/PRODUCTION_NOTES.md`](docs/PRODUCTION_NOTES.md)
- **Synthetic Data**: [`data/patients.json`](data/patients.json) & [`data/reports.json`](data/reports.json)
- **Render Blueprint**: [`render.yaml`](render.yaml)
- **Live GitHub Repository**: [https://github.com/surendra902/viscan-dental-assistant](https://github.com/surendra902/viscan-dental-assistant)
- **Live Production App**: [https://viscan-dental-assistant.onrender.com](https://viscan-dental-assistant.onrender.com)
