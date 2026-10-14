# Viscan AI Dental Assistant -- Documented Demo Sequence

This document provides a documented sequence of API calls with verbatim sample outputs, satisfying the demonstration requirement (PDF p2 §4: *"documented sequence of API calls with sample outputs"*).

Base URL: `http://localhost:8000`

---

## 1. Health & Synthetic Dataset Check

### Request
```bash
curl -X GET "http://localhost:8000/health"
```

### Response
```json
{
  "status": "healthy",
  "service": "viscan-dental-assistant",
  "mock_patients_loaded": 6,
  "mock_reports_loaded": 13
}
```

---

## 2. Feature A: Correct Report Retrieval (Mandatory)

### Scenario
Clinician asks: *"Open Priya Sharma's latest OPG report"*

### Request
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Open Priya Sharma'\''s latest OPG report",
    "session_id": "demo-session-1"
  }'
```

### Response
```json
{
  "session_id": "demo-session-1",
  "intent": "retrieve_report",
  "response_text": "Retrieved OPG report for Priya Sharma (P001) dated 2026-01-15:\nReferring Doctor: Dr. Rajesh Kulkarni\nFindings:\n  • Lower right third molar (tooth 48) is horizontally impacted with crown approximating the distal root of tooth 47.\n  • Mild periapical radiolucency associated with the mesial root apex of tooth 36, suggestive of chronic apical periodontitis.\n  • Alveolar bone crest levels are generally within normal limits across both arches.\n  • Bilateral temporomandibular joints appear symmetrical with normal condylar morphology.\nImpression: 1. Horizontally impacted tooth 48 requiring surgical evaluation. 2. Chronic periapical lesion on tooth 36.",
  "status": "success",
  "patient": {
    "patient_id": "P001",
    "name": "Priya Sharma",
    "date_of_birth": "1997-04-12",
    "gender": "Female",
    "contact": "+91-98765-01001"
  },
  "report": {
    "report_id": "R101",
    "patient_id": "P001",
    "modality": "OPG",
    "date": "2026-01-15T10:30:00Z",
    "referring_doctor": "Dr. Rajesh Kulkarni",
    "clinical_indication": "Evaluation of recurrent pain in lower right posterior quadrant",
    "findings": [
      "Lower right third molar (tooth 48) is horizontally impacted with crown approximating the distal root of tooth 47.",
      "Mild periapical radiolucency associated with the mesial root apex of tooth 36, suggestive of chronic apical periodontitis.",
      "Alveolar bone crest levels are generally within normal limits across both arches.",
      "Bilateral temporomandibular joints appear symmetrical with normal condylar morphology."
    ],
    "impression": "1. Horizontally impacted tooth 48 requiring surgical evaluation. 2. Chronic periapical lesion on tooth 36.",
    "evidence_snippet": "Report R101 (OPG, 2026-01-15): Horizontally impacted tooth 48; periapical radiolucency tooth 36."
  },
  "candidates": null,
  "evidence": {
    "report_id": "R101",
    "patient_id": "P001",
    "modality": "OPG",
    "date": "2026-01-15T10:30:00Z",
    "findings": [
      "Lower right third molar (tooth 48) is horizontally impacted with crown approximating the distal root of tooth 47.",
      "Mild periapical radiolucency associated with the mesial root apex of tooth 36, suggestive of chronic apical periodontitis.",
      "Alveolar bone crest levels are generally within normal limits across both arches.",
      "Bilateral temporomandibular joints appear symmetrical with normal condylar morphology."
    ],
    "impression": "1. Horizontally impacted tooth 48 requiring surgical evaluation. 2. Chronic periapical lesion on tooth 36.",
    "evidence_snippet": "Report R101 (OPG, 2026-01-15): Horizontally impacted tooth 48; periapical radiolucency tooth 36."
  },
  "tool_calls": [
    {
      "tool": "find_patient",
      "arguments": { "name": "Priya Sharma" },
      "result_count": 1
    },
    {
      "tool": "get_latest_report",
      "arguments": { "patient_id": "P001", "modality": "OPG" }
    }
  ]
}
```

---

## 3. Feature A: Ambiguous Patient Identity Handling (Mandatory)

### Scenario
Clinician asks: *"Open Priya's latest OPG report"* without specifying the last name. The mock dataset contains two similar names: **Priya Sharma (P001)** and **Priya Menon (P002)**.

### Request
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Open Priya'\''s latest OPG report",
    "session_id": "demo-session-2"
  }'
```

### Response
```json
{
  "session_id": "demo-session-2",
  "intent": "retrieve_report",
  "response_text": "Multiple patients found matching 'Priya': Priya Sharma (ID: P001), Priya Menon (ID: P002). Please specify the exact full name or patient ID to proceed.",
  "status": "ambiguous",
  "patient": null,
  "report": null,
  "candidates": [
    {
      "patient_id": "P001",
      "name": "Priya Sharma",
      "date_of_birth": "1997-04-12",
      "gender": "Female",
      "contact": "+91-98765-01001"
    },
    {
      "patient_id": "P002",
      "name": "Priya Menon",
      "date_of_birth": "1992-09-18",
      "gender": "Female",
      "contact": "+91-98765-01002"
    }
  ],
  "evidence": null,
  "tool_calls": [
    {
      "tool": "find_patient",
      "arguments": { "name": "Priya" },
      "result_count": 2
    }
  ]
}
```
*Note: The system never guesses; it safely halts and returns candidate options.*

---

## 4. Feature C: Context-Dependent Follow-Up (Mandatory)

### Scenario
In the same session after retrieving Priya Sharma's report (Turn 1), the clinician asks: *"Summarize her report"* (Turn 2). The system resolves the pronoun `"her"` unambiguously to Priya Sharma (P001) without asking again, and presents ground-truth evidence.

### Request
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Summarize her report",
    "session_id": "demo-session-1"
  }'
```

### Response
```json
{
  "session_id": "demo-session-1",
  "intent": "follow_up_summary",
  "response_text": "Summary for Priya Sharma (OPG dated 2026-01-15):\n- Clinical Indication: Evaluation of recurrent pain in lower right posterior quadrant\n- Key Findings:\n  * Lower right third molar (tooth 48) is horizontally impacted with crown approximating the distal root of tooth 47.\n  * Mild periapical radiolucency associated with the mesial root apex of tooth 36, suggestive of chronic apical periodontitis.\n  * Alveolar bone crest levels are generally within normal limits across both arches.\n  * Bilateral temporomandibular joints appear symmetrical with normal condylar morphology.\n- Diagnostic Impression: 1. Horizontally impacted tooth 48 requiring surgical evaluation. 2. Chronic periapical lesion on tooth 36.",
  "status": "success",
  "patient": {
    "patient_id": "P001",
    "name": "Priya Sharma",
    "date_of_birth": "1997-04-12",
    "gender": "Female",
    "contact": "+91-98765-01001"
  },
  "report": {
    "report_id": "R101",
    "patient_id": "P001",
    "modality": "OPG",
    "date": "2026-01-15T10:30:00Z",
    "referring_doctor": "Dr. Rajesh Kulkarni",
    "clinical_indication": "Evaluation of recurrent pain in lower right posterior quadrant",
    "findings": [
      "Lower right third molar (tooth 48) is horizontally impacted with crown approximating the distal root of tooth 47.",
      "Mild periapical radiolucency associated with the mesial root apex of tooth 36, suggestive of chronic apical periodontitis.",
      "Alveolar bone crest levels are generally within normal limits across both arches.",
      "Bilateral temporomandibular joints appear symmetrical with normal condylar morphology."
    ],
    "impression": "1. Horizontally impacted tooth 48 requiring surgical evaluation. 2. Chronic periapical lesion on tooth 36.",
    "evidence_snippet": "Report R101 (OPG, 2026-01-15): Horizontally impacted tooth 48; periapical radiolucency tooth 36."
  },
  "candidates": null,
  "evidence": {
    "report_id": "R101",
    "patient_id": "P001",
    "modality": "OPG",
    "date": "2026-01-15T10:30:00Z",
    "findings": [
      "Lower right third molar (tooth 48) is horizontally impacted with crown approximating the distal root of tooth 47.",
      "Mild periapical radiolucency associated with the mesial root apex of tooth 36, suggestive of chronic apical periodontitis.",
      "Alveolar bone crest levels are generally within normal limits across both arches.",
      "Bilateral temporomandibular joints appear symmetrical with normal condylar morphology."
    ],
    "impression": "1. Horizontally impacted tooth 48 requiring surgical evaluation. 2. Chronic periapical lesion on tooth 36.",
    "evidence_snippet": "Report R101 (OPG, 2026-01-15): Horizontally impacted tooth 48; periapical radiolucency tooth 36."
  },
  "tool_calls": [
    {
      "tool": "get_report_evidence",
      "arguments": { "report_id": "R101" }
    }
  ]
}
```

---

## 5. Feature B: Clinical Dictation to Draft Report (Mandatory)

### Scenario
Clinician dictates: *"Lower right third molar is horizontally impacted"*

### Request
```bash
curl -X POST "http://localhost:8000/dictate" \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "Lower right third molar is horizontally impacted",
    "session_id": "demo-session-dictate"
  }'
```

### Response
```json
{
  "session_id": "demo-session-dictate",
  "transcript": "Lower right third molar is horizontally impacted",
  "structured_findings": [
    {
      "anatomical_site": "Lower right third molar",
      "observation": "horizontally impacted",
      "confidence": 0.95,
      "is_supported": true
    }
  ],
  "draft_report": "CLINICAL OBSERVATION REPORT (DRAFT - REQUIRES CLINICIAN REVIEW)\n\nRaw Dictation: \"Lower right third molar is horizontally impacted\"\n\nStructured Observations:\n - [VALIDATED] Site: Lower right third molar | Observation: horizontally impacted (Confidence: 0.95)\n\nStatus: DRAFT - Mandatory clinician sign-off required prior to final diagnostic record.",
  "uncertainties": [],
  "unsupported_claims": [],
  "requires_review": true
}
```

---

## 6. Feature B: Unsupported Clinical Claims Interception (Mandatory)

### Scenario
Clinician dictates hallucinatory or unsupported concepts: *"Patient has dragon teeth with quantum decay"*

### Request
```bash
curl -X POST "http://localhost:8000/dictate" \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "Patient has dragon teeth with quantum decay",
    "session_id": "demo-session-unsupported"
  }'
```

### Response
```json
{
  "session_id": "demo-session-unsupported",
  "transcript": "Patient has dragon teeth with quantum decay",
  "structured_findings": [
    {
      "anatomical_site": "dragon teeth",
      "observation": "quantum decay",
      "confidence": 0.3,
      "is_supported": false
    }
  ],
  "draft_report": "CLINICAL OBSERVATION REPORT (DRAFT - REQUIRES CLINICIAN REVIEW)\n\nRaw Dictation: \"Patient has dragon teeth with quantum decay\"\n\nStructured Observations:\n - [UNSUPPORTED / CAUTION] Site: dragon teeth | Observation: quantum decay (Confidence: 0.30)\n\nClinician Flags / Unsupported Claims:\n * WARNING: Unrecognized or non-standard clinical entity: 'dragon teeth'.\n * WARNING: Unrecognized or non-standard clinical entity: 'quantum decay'.\n * WARNING: Finding 'quantum decay' at site 'dragon teeth' contains unsupported or unverified dental terminology.\n\nStatus: DRAFT - Mandatory clinician sign-off required prior to final diagnostic record.",
  "uncertainties": [
    "High risk finding: 'dragon teeth' is not a recognized dental clinical condition.",
    "High risk finding: 'quantum decay' is not a recognized dental clinical condition.",
    "Unverified clinical claim: 'dragon teeth - quantum decay' flagged for mandatory clinician review."
  ],
  "unsupported_claims": [
    "Unrecognized or non-standard clinical entity: 'dragon teeth'.",
    "Unrecognized or non-standard clinical entity: 'quantum decay'.",
    "Finding 'quantum decay' at site 'dragon teeth' contains unsupported or unverified dental terminology."
  ],
  "requires_review": true
}
```
*Note: Fictitious observations are flagged, confidence penalized to 0.30, marked `is_supported: false`, explicit warnings generated, and `requires_review` set to true.*

---

## 7. Voice / STT Intake Stub (Mandatory Voice Support)

### Request
```bash
curl -X POST "http://localhost:8000/transcribe" \
  -F "transcript_fallback=Lower right third molar is horizontally impacted"
```

### Response
```json
{
  "transcript": "Lower right third molar is horizontally impacted",
  "source": "typed_transcript"
}
```
*(Accepts audio file via `-F "audio=@path/to/dictation.wav"` as well, automatically invoking Whisper if OPENAI_API_KEY is present).*
