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
             |    LLM Engine Layer   |                         |  Candidate Extractor  |
             |   (Intent & Slots)    |                         |  (Site & Observation) |
             +-----------------------+                         +-----------------------+
                         |                                                 |
                         | tool call arguments                             | raw candidate findings
                         v                                                 v
             +-----------------------+                         +-----------------------+
             |  Deterministic Tools  |                         | Business-Rule Layer   |
             |  - find_patient       |                         | (validators.py)       |
             |  - get_latest_report  |                         | - Dental Allowlist    |
             |  - list_reports       |                         | - Fictitious Filter   |
             +-----------------------+                         | - Uncertainty Label   |
                         |                                     | - requires_review: true|
                         v                                     +-----------------------+
             +-----------------------+                                     |
             |   Synthetic Store     |                                     v
             | (patients / reports)  |                         +-----------------------+
             +-----------------------+                         | Editable JSON + Draft |
                         |                                     +-----------------------+
                         v
             +-----------------------+
             | Grounded Response     |
             | + Auditable Evidence  |
             +-----------------------+
```

---

## 1. Voice & Speech-to-Text (STT) Intake Flow
- **Endpoint**: `POST /transcribe`
- **Supported Formats**: Accepts multipart audio file (`audio/wav`, `audio/mp3`, `audio/webm`) or fallback text transcript.
- **Provider Layer**:
  - In production with `OPENAI_API_KEY`: streams audio directly to Whisper API (`whisper-1`).
  - In offline / CI test mode: provides deterministic clinical transcription (e.g., *"Lower right third molar is horizontally impacted"*) to ensure tests pass without paid keys.

---

## 2. LLM Intent & Dialogue Flow (Feature A & C)
- **Endpoint**: `POST /chat`
- **Session Context**: Keyed by `session_id` using in-memory `SessionManager`. Tracks `last_patient_id`, `last_report_id`, and `last_modality` across conversational turns.
- **Intent Disambiguation & Safe Execution**:
  1. **Pronoun / Follow-Up Detection**: Resolves pronouns (*"Summarize her report"*, *"What did her OPG show?"*) directly using the active session state without re-prompting the clinician. Returns the summary coupled with explicit report evidence.
  2. **Patient Lookup**: Extracts name entities and executes deterministic tool `find_patient(name)`.
     - **0 Matches**: Returns safe `not_found` response without hallucinating records.
     - **>1 Matches (Ambiguity)**: E.g., *"Priya"* matches *Priya Sharma (P001)* and *Priya Menon (P002)*. The system halts retrieval, emits `status: ambiguous`, lists candidate IDs/names, and requests explicit clarification. It never guesses.
     - **1 Match**: Invokes `get_latest_report(patient_id, modality)`. If report exists, returns report details and attaches structured `evidence` payload. If the modality doesn't exist (e.g. Sara Khan's CBCT), safely reports missing report status.

---

## 3. Tool & Business Validation Layer Separation (PDF §3)
Per technical guidelines, **the LLM is strictly decoupled from business validation**:
- The LLM interprets language, extracts parameters, and suggests candidate slots.
- Python deterministic logic (`app/validators.py`) enforces clinical sanity:
  - **Dental Anatomical Allowlist**: Validates tooth numbering (FDI / Universal), arches (maxillary, mandibular), quadrants, bone structures (alveolar ridge, ramus, condyle), and soft tissues.
  - **Pathology Controlled Vocabulary**: Validates recognized dental conditions (impaction, caries, periapical radiolucency, bone loss, periodontal defects).
  - **Fictitious / Non-Dental Interceptor**: Terms like *"dragon teeth"* or *"quantum decay"* are detected and routed into `unsupported_claims`. Confidence is curtailed to ≤ 0.30, and `is_supported` is set to `false`.
  - **Clinical Safety Guarantee**: `requires_review` is hardcoded to `True` for all draft reports. Clinician sign-off is mandatory.

---

## 4. Report Generation & Evidence Grounding Flow
1. Audio or transcript arrives at `/dictate`.
2. Structured slots (`anatomical_site`, `observation`, `confidence`) are produced.
3. Validator scrubs each finding, attaches uncertainty flags if ambiguous markers are found, and compiles a clean, readable clinical draft.
4. Response returns both human-readable text and machine-editable JSON with full audit flags.
