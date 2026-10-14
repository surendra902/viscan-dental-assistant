# Viscan AI Dental Assistant -- Architecture Document

## System Flow & Component Overview

```
                               +-------------------------------------+
                               | Clinician (Audio / Dictation / Text)|
                               +-------------------------------------+
                                                  |
                                                  v
                               +-------------------------------------+
                               |            FastAPI API              |
                               |  /chat  |  /dictate  |  /transcribe |
                               +-------------------------------------+
                                                  |
                         +------------------------+------------------------+
                         |                                                 |
                         v                                                 v
           [ Feature A & C: Dialogue ]                       [ Feature B: Clinical Dictation ]
                         |                                                 |
                         v                                                 v
             +-----------------------+                         +-----------------------+
             | Deterministic Parser  |                         |  Candidate Extractor  |
             | (Intent & Slot Engine)|                         | OpenRouter Nemotron / |
             +-----------------------+                         | Deterministic Fallback|
                         |                                     +-----------------------+
                         | deterministic tool arguments                    |
                         v                                                 | raw candidate findings
             +-----------------------+                                     v
             |  Deterministic Tools  |                         +-----------------------+
             |  - find_patient       |                         | Business-Rule Layer   |
             |  - get_latest_report  |                         | (validators.py)       |
             |  - list_reports       |                         | - Dental Allowlist    |
             +-----------------------+                         | - Whole-Token Number  |
                         |                                     | - Laterality Guard    |
                         v                                     | - Clause Binding      |
             +-----------------------+                         | - Negation Alignment  |
             |   Synthetic Store     |                         | - requires_review: true|
             | (patients / reports)  |                         +-----------------------+
             +-----------------------+                                     |
                         |                                                 v
                         v                                     +-----------------------+
             +-----------------------+                         | Editable JSON + Draft |
             | Grounded Response     |                         +-----------------------+
             | + Auditable Evidence  |
             +-----------------------+
```

---

## 1. Voice & Speech-to-Text (STT) Intake Flow
- **Endpoint**: `POST /transcribe`
- **Supported Formats**: Accepts multipart audio file (`audio/wav`, `audio/mp3`, `audio/webm`) or client-side Web Speech API transcription.
- **Provider Layer**:
  - In production with `OPENAI_API_KEY`: streams audio directly to Whisper API (`whisper-1`).
  - In offline / CI test mode: provides deterministic clinical transcription (e.g., *"Lower right third molar is horizontally impacted"*) to ensure tests pass without paid keys.
  - Safe failure mode: on microphone error or permission rejection, client-side input is strictly preserved and no synthetic observations are auto-submitted.

---

## 2. Deterministic Dialogue & Retrieval Flow (Feature A & C)
- **Endpoint**: `POST /chat`
- **Session Context**: Keyed by `session_id` using in-memory `SessionManager`. Tracks `last_patient_id`, `last_report_id`, and `last_modality` across conversational turns.
- **Intent Disambiguation & Safe Execution**:
  1. **Explicit Patient Recognition**: Resolves explicitly named patients before checking pronoun context. If a user asks *"Summarize Sara Khan's report"*, Sara Khan is resolved directly, never inheriting previous patient context.
  2. **Pronoun / Follow-Up Detection**: Resolves pronouns (*"Summarize her report"*, *"What were the findings?"*) using the active session state only when no different patient is named.
  3. **Patient Lookup**: Executes deterministic tool `find_patient(name)`.
     - **0 Matches**: Returns safe `not_found` response without hallucinating records.
     - **>1 Matches (Ambiguity)**: E.g., *"Priya"* matches *Priya Sharma (P001)* and *Priya Menon (P002)*. The system halts retrieval, emits `status: ambiguous`, lists candidate IDs/names, and requests explicit clarification.
     - **1 Match**: Invokes `get_latest_report(patient_id, modality)`. If report exists, returns report details and attaches structured `evidence` payload. If the requested modality doesn't exist (e.g. Sara Khan's CBCT), safely reports missing report status.

---

## 3. Tool & Business Validation Layer Separation (PDF §3)
Per technical guidelines, **the extraction layer is strictly decoupled from business validation**:
- The candidate extractor parses natural language into initial slots (`anatomical_site`, `observation`, `confidence`).
- Python deterministic logic (`app/validators.py`) enforces clinical sanity:
  - **Dental Anatomical Allowlist**: Validates tooth numbering (Universal 1–32, FDI permanent 11–48, deciduous 51–85), arches, quadrants, and structures.
  - **Pathology Controlled Vocabulary**: Validates recognized dental conditions (impaction, caries, periapical radiolucency, bone loss, periodontal defects).
  - **Semantic Grounding & Fictitious Interceptor**:
    - Fictitious terms (*"dragon teeth"*, *"quantum decay"*) are isolated to `unsupported_claims` with confidence reduced to 0.30.
    - Whole-token tooth number matching prevents substring misattributions (e.g., tooth 16 mistaken for tooth 6).
    - Laterality verification prevents left/right switches.
    - Clause binding prevents pathology reassignments across different clauses.
    - Negation alignment flags removal or invention of clinical negation.
  - **Draft Status Labeling**: `requires_review` is set to `True` on every generated draft, labeling it as a draft requiring human clinician verification.

---

## 4. Report Generation & Evidence Grounding Flow
1. Audio or transcript arrives at `/dictate`.
2. Structured slots (`anatomical_site`, `observation`, `confidence`) are produced via OpenRouter Nemotron (or local fallback).
3. Validator scrubs each finding, attaches uncertainty flags if ambiguous markers are found, and compiles a clean, readable clinical draft.
4. Response returns both human-readable text and machine-editable JSON with full audit flags.
