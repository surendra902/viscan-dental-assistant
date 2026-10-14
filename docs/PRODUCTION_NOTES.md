# Viscan AI Dental Assistant -- Production Considerations

This document addresses productionization requirements specified in Section 3 of the technical assessment: **Privacy**, **Authorization**, **Latency**, **Cost**, and **Failure Handling**.

---

## 1. Privacy & PHI Protection
- **De-Identification & Zero Real PHI**: Production systems must comply with HIPAA / GDPR / Indian Digital Personal Data Protection (DPDP) Act.
  - In this proof of concept, 100% of the patient and imaging report data is synthetic.
  - In production, real patient names, IDs, dates of birth, and contact numbers should never be logged to external observability platforms (Datadog, CloudWatch) in plaintext.
  - PII masking proxies (e.g., Presidio or local tokenizers) should strip PHI before transmitting queries to external commercial LLM APIs, or on-premise/self-hosted HIPAA-compliant model instances (e.g., Azure OpenAI HIPAA agreement, AWS Bedrock) should be utilized.
- **Session Ephemerality**: In-memory conversational state should have a tight TTL (e.g., 15 minutes of inactivity) and be encrypted at rest in Redis or relational databases with column-level encryption.

---

## 2. Authorization & Access Control (RBAC)
- **Role-Based Access Control**:
  - `Radiologist / Clinician`: Read/write access to draft dictations, view imaging reports, approve final clinical notes.
  - `Dental Assistant / Receptionist`: Access to appointment booking and report retrieval, but no authorization to modify clinical dictations.
  - `Auditor`: Read-only access to access logs and ground-truth evidence trails.
- **Audit Trails**: Every retrieval of a patient report (`find_patient`, `get_latest_report`) must produce an immutable audit log storing `user_id`, `timestamp`, `patient_id`, and `report_id` to satisfy medical device and radiology compliance audits.

---

## 3. Latency Optimization
- **Target SLA**: End-to-end response < 1.5s for conversational queries; < 800ms for dictation drafting.
- **Bottleneck Analysis**:
  - Deterministic tools (`find_patient`, `get_latest_report`) execute in `< 1ms` in memory.
  - External LLM inference (e.g., GPT-4o) typically consumes 800ms - 2000ms.
  - STT transcription (Whisper) consumes 500ms - 1500ms depending on audio length.
- **Optimization Strategy**:
  - **Streaming Responses**: Stream tokens to frontend UI to decrease Time-to-First-Token (TTFT) to < 300ms.
  - **Fast Rule Pre-Filtering**: Deterministic regex and local embedding lookups can resolve common exact-match retrievals without invoking external LLMs, dropping latency to < 10ms for 80% of standard retrieval requests.

---

## 4. Cost Engineering & Model Economics
- **STT (Speech-to-Text)**:
  - OpenAI Whisper API: ~$0.006 per minute. An average dental dictation is 30 seconds (~$0.003/dictation).
  - Open-source self-hosted Whisper (faster-whisper on local T4/A10 GPU): Fixed hardware cost, ~$0.0004/minute at high volume.
- **LLM Reasoning**:
  - Structured extraction & intent parsing does not require expensive frontier frontier reasoning models (e.g., Claude 3.5 Sonnet / GPT-4o).
  - High-efficiency models like `gpt-4o-mini` ($0.15 / 1M input tokens, $0.60 / 1M output tokens) or Claude 3.5 Haiku cost less than **$0.0003 per turn**.
  - In offline / mock mode: $0.00.

---

## 5. Failure Handling & Clinical Safety
- **Hallucination Interception**: The business-rule validator (`app/validators.py`) rejects unverified entities (*"dragon teeth"*, *"quantum decay"*) regardless of what the LLM generates.
- **Mandatory Review Flag**: `requires_review: true` ensures that no AI-generated draft report can ever be saved directly into an Electronic Health Record (EHR) or PACS without explicit human clinician sign-off.
- **Graceful Degradation**:
  - If STT audio is garbled or corrupted, the system prompts the doctor to repeat or switch to typed transcript.
  - If patient identity is ambiguous, the system never guesses; it prompts for explicit disambiguation.
