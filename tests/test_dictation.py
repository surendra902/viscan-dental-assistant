import pytest
from fastapi.testclient import TestClient

def test_unsupported_clinical_claims(client: TestClient):
    """
    Test 3 (Required by PDF p2 s3): Unsupported clinical claims.
    Given fictitious/hallucinatory input: 'Patient has dragon teeth with quantum decay'
    Must:
      1. Flag unsupported claims in `unsupported_claims`
      2. Label uncertainty in `uncertainties`
      3. Set `requires_review: True`
      4. NOT invent valid observations or silently accept fictitious entities.
    """
    transcript = "Patient has dragon teeth with quantum decay"
    response = client.post("/dictate", json={
        "transcript": transcript,
        "session_id": "test-session-unsupported"
    })

    assert response.status_code == 200
    data = response.json()

    assert data["requires_review"] is True
    assert len(data["unsupported_claims"]) > 0
    assert len(data["uncertainties"]) > 0

    # Ensure unsupported terminology is explicitly flagged
    claims_text = " ".join(data["unsupported_claims"]).lower()
    assert "dragon teeth" in claims_text or "quantum decay" in claims_text

    # Ensure findings are marked as unsupported
    for finding in data["structured_findings"]:
        if "dragon" in finding["anatomical_site"].lower() or "quantum" in finding["observation"].lower():
            assert finding["is_supported"] is False

    # Check that draft report includes warning flags
    assert "WARNING" in data["draft_report"] or "CAUTION" in data["draft_report"]

def test_valid_clinical_dictation(client: TestClient):
    """
    Feature B (Mandatory, PDF p1 s1B):
    Given: 'Lower right third molar is horizontally impacted'
    Must: Produce editable structured JSON with findings, anatomical site,
          and a readable draft report with clinician review required.
    """
    transcript = "Lower right third molar is horizontally impacted"
    response = client.post("/dictate", json={
        "transcript": transcript,
        "session_id": "test-session-dictate"
    })

    assert response.status_code == 200
    data = response.json()

    assert data["requires_review"] is True
    assert len(data["structured_findings"]) >= 1

    first_finding = data["structured_findings"][0]
    assert "lower right third molar" in first_finding["anatomical_site"].lower()
    assert "horizontally impacted" in first_finding["observation"].lower()
    assert first_finding["is_supported"] is True
    assert first_finding["confidence"] >= 0.80

    # Readable draft report must be present
    assert "CLINICAL OBSERVATION REPORT (DRAFT" in data["draft_report"]
    assert "Lower right third molar" in data["draft_report"]

def test_transcribe_endpoint(client: TestClient):
    """
    Voice/STT endpoint verification (PDF p2 note: clearly supports voice input).
    """
    # Test typed fallback
    r1 = client.post("/transcribe", data={"transcript_fallback": "Deep occlusal caries on tooth 16"})
    assert r1.status_code == 200
    assert r1.json()["transcript"] == "Deep occlusal caries on tooth 16"
    assert r1.json()["source"] == "typed_transcript"

    # Test audio upload simulation
    fake_audio = b"RIFF....WAVEfmt ...."
    files = {"audio": ("sample_dictation.wav", fake_audio, "audio/wav")}
    r2 = client.post("/transcribe", files=files)
    assert r2.status_code == 200
    assert len(r2.json()["transcript"]) > 0
    assert r2.json()["source"] in ["whisper_api", "mock_stt_audio"]
