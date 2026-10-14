import os
import sys
import time
import json
import urllib.request
import urllib.error
import urllib.parse

BASE = os.getenv("TARGET_URL", "http://127.0.0.1:8000").rstrip("/")

def request(method, path, data=None, is_json=True):
    url = BASE + path
    headers = {}
    body = None
    if data is not None:
        if is_json:
            headers["Content-Type"] = "application/json"
            body = json.dumps(data).encode("utf-8")
        else:
            headers["Content-Type"] = "application/x-www-form-urlencoded"
            body = urllib.parse.urlencode(data).encode("utf-8")

    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            elapsed_ms = (time.perf_counter() - t0) * 1000
            res_body = resp.read().decode("utf-8")
            status = resp.status
            return status, json.loads(res_body) if res_body else {}, elapsed_ms
    except urllib.error.HTTPError as e:
        elapsed_ms = (time.perf_counter() - t0) * 1000
        res_body = e.read().decode("utf-8")
        return e.code, json.loads(res_body) if res_body else {}, elapsed_ms
    except Exception as e:
        elapsed_ms = (time.perf_counter() - t0) * 1000
        return 500, {"error": str(e)}, elapsed_ms

print(f"=== STARTING AUDIT RUN ON {BASE} ===")

tests = [
    ("Health Check", "GET", "/health", None, True, lambda s, p: s == 200 and p.get("status") == "healthy"),
    ("Patient Directory", "GET", "/patients", None, True, lambda s, p: s == 200 and len(p) >= 6),
    ("Patient Reports Existing (P001)", "GET", "/reports/P001", None, True, lambda s, p: s == 200 and len(p) >= 2),
    ("Patient Reports Nonexistent (P999)", "GET", "/reports/P999", None, True, lambda s, p: s == 404),
    ("Feature A: Exact Retrieval (Priya Sharma OPG)", "POST", "/chat", {"message": "Open Priya Sharma's latest OPG report", "session_id": "audit-1"}, True, lambda s, p: s == 200 and p.get("report", {}).get("report_id") == "R101"),
    ("Feature A: Ambiguous Identity (Priya OPG)", "POST", "/chat", {"message": "Open Priya's latest OPG report", "session_id": "audit-2"}, True, lambda s, p: s == 200 and p.get("status") == "ambiguous"),
    ("Feature A: Disambiguation Modality Retention", "POST", "/chat", {"message": "Priya Sharma", "session_id": "audit-2"}, True, lambda s, p: s == 200 and p.get("report", {}).get("report_id") == "R101"),
    ("Feature A: Missing Report (Sara Khan CBCT)", "POST", "/chat", {"message": "Open Sara Khan's latest CBCT report", "session_id": "audit-3"}, True, lambda s, p: s == 200 and p.get("status") == "not_found" and p.get("report") is None),
    ("Feature A: Patient Switch Does Not Leak Report", "POST", "/chat", {"message": "Summarize her report", "session_id": "audit-3"}, True, lambda s, p: s == 200 and (p.get("report") is None or p.get("report", {}).get("patient_id") == "P004")),
    ("Feature C: Follow-up Unambiguous (Priya Sharma)", "POST", "/chat", {"message": "Summarize her report", "session_id": "audit-1"}, True, lambda s, p: s == 200 and p.get("report", {}).get("patient_id") == "P001"),
    ("Feature C: Explicit Switch In Follow-up (Sara Khan)", "POST", "/chat", {"message": "Summarize Sara Khan's report", "session_id": "audit-1"}, True, lambda s, p: s == 200 and p.get("report", {}).get("patient_id") == "P004"),
    ("Feature C: Follow-up With No Prior Context", "POST", "/chat", {"message": "Summarize her report", "session_id": "audit-empty"}, True, lambda s, p: s == 200 and p.get("status") == "ambiguous"),
    ("Feature B: Valid Dictation", "POST", "/dictate", {"transcript": "Lower right third molar is horizontally impacted", "session_id": "audit-1"}, True, lambda s, p: s == 200 and p.get("structured_findings", [{}])[0].get("is_supported") is True),
    ("Feature B: Unsupported Claims Dictation", "POST", "/dictate", {"transcript": "Patient has dragon teeth with quantum decay", "session_id": "audit-1"}, True, lambda s, p: s == 200 and len(p.get("unsupported_claims", [])) > 0),
    ("Feature B: Impossible Tooth Rejected", "POST", "/dictate", {"transcript": "Tooth 99 has caries", "session_id": "audit-1"}, True, lambda s, p: s == 200 and p.get("structured_findings", [{}])[0].get("is_supported") is False),
    ("Feature B: Source Uncertainty Preservation", "POST", "/dictate", {"transcript": "Possible caries in tooth 16", "session_id": "audit-1"}, True, lambda s, p: s == 200 and len(p.get("uncertainties", [])) > 0),
    ("Voice Intake: Typed Transcript Fallback", "POST", "/transcribe", {"transcript_fallback": "Deep occlusal caries on tooth 16"}, False, lambda s, p: s == 200 and p.get("source") == "typed_transcript"),
]

all_passed = True
for name, method, path, data, is_json, validator in tests:
    status, payload, ms = request(method, path, data, is_json)
    try:
        passed = validator(status, payload)
    except Exception:
        passed = False

    if not passed:
        all_passed = False
    print(f"[{'PASS' if passed else 'FAIL'}] {name} -> Status: {status} | Latency: {ms:.1f}ms")

if not all_passed:
    sys.exit(1)
print("\n=== ALL AUDIT BENCHMARKS VERIFIED SUCCESSFULLY ===")
