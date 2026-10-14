import time
import json
import urllib.request
import urllib.error
import urllib.parse

BASE = "http://127.0.0.1:8000"

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
        with urllib.request.urlopen(req, timeout=10) as resp:
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

print("=== STARTING AUDIT RUN ===")

tests = [
    ("Health Check", "GET", "/health", None, True),
    ("Patient Directory", "GET", "/patients", None, True),
    ("Patient Reports Existing (P001)", "GET", "/reports/P001", None, True),
    ("Patient Reports Nonexistent (P999)", "GET", "/reports/P999", None, True),
    ("Feature A: Exact Retrieval (Priya Sharma OPG)", "POST", "/chat", {"message": "Open Priya Sharma's latest OPG report", "session_id": "audit-1"}, True),
    ("Feature A: Ambiguous Identity (Priya OPG)", "POST", "/chat", {"message": "Open Priya's latest OPG report", "session_id": "audit-2"}, True),
    ("Feature A: Missing Report (Sara Khan CBCT)", "POST", "/chat", {"message": "Open Sara Khan's latest CBCT report", "session_id": "audit-3"}, True),
    ("Feature A: Patient ID lookup (P003 CBCT)", "POST", "/chat", {"message": "Open P003's CBCT report", "session_id": "audit-4"}, True),
    ("Feature C: Follow-up Unambiguous (Summarize her report)", "POST", "/chat", {"message": "Summarize her report", "session_id": "audit-1"}, True),
    ("Feature C: Follow-up With No Prior Context", "POST", "/chat", {"message": "Summarize her report", "session_id": "audit-empty"}, True),
    ("Feature B: Valid Dictation", "POST", "/dictate", {"transcript": "Lower right third molar is horizontally impacted", "session_id": "audit-1"}, True),
    ("Feature B: Unsupported Claims Dictation", "POST", "/dictate", {"transcript": "Patient has dragon teeth with quantum decay", "session_id": "audit-1"}, True),
    ("Feature B: Clinical Uncertainty Dictation", "POST", "/dictate", {"transcript": "Mild periapical radiolucency suggestive of apical periodontitis on tooth 36", "session_id": "audit-1"}, True),
    ("Voice Intake: Typed Transcript Fallback", "POST", "/transcribe", {"transcript_fallback": "Deep occlusal caries on tooth 16"}, False),
]

results = []
for name, method, path, data, is_json in tests:
    status, payload, ms = request(method, path, data, is_json)
    passed = status in [200, 404]
    results.append((name, status, ms, payload))
    print(f"[{'PASS' if passed else 'FAIL'}] {name} -> Status: {status} | Latency: {ms:.1f}ms")

print("\n=== DETAILED FINDINGS ===")
for name, status, ms, payload in results:
    if "Feature" in name:
        print(f"\n--- {name} ---")
        print(f"Status: {status} ({ms:.1f}ms)")
        print(json.dumps(payload, indent=2)[:400] + "...")
