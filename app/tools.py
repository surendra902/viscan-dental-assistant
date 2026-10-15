import re
from typing import List, Optional, Dict, Any
from app.models import Patient, Report
from app.data_store import DataStore, data_store

def normalize_patient_id(text: str) -> Optional[str]:
    """
    Normalizes spoken or typed patient ID variations:
    e.g. 'P 006', 'P 0 0 6', 'patient ID P 006', 'PID p004', 'ID P 6', 'p001' -> 'P006', 'P004', 'P001'
    """
    if not text:
        return None
    # 1. Standalone or prefixed 'P' followed by digits (with optional spaces/dashes)
    m = re.search(r'\b(?:(?:patient\s*(?:id)?|pid|id)\s*:?\s*)?p\s*[-_ ]*(\d[\d\s]{0,4}\d|\d)\b', text, re.IGNORECASE)
    if not m:
        # 2. 'patient ID' or 'PID' followed by digits without 'P'
        m = re.search(r'\b(?:patient\s*(?:id)?|pid)\s*:?\s*(\d[\d\s]{0,4}\d|\d)\b', text, re.IGNORECASE)
    if m:
        digits = re.sub(r'\D', '', m.group(1))
        if digits:
            return f"P{int(digits):03d}"
    return None

def find_patient(name: str, store: DataStore = data_store) -> List[Patient]:
    """
    Search for patients by full or partial name, or patient ID.
    Returns 0, 1, or multiple matches (triggering disambiguation).
    """
    cleaned = name.strip()
    cleaned = cleaned.strip(" \t\n\r.?!,;:")
    if not cleaned:
        return []

    # 1. Check for normalized patient ID match (e.g. "P 006", "patient id p 006", "PID p004")
    norm_id = normalize_patient_id(cleaned)
    if norm_id:
        id_matches = [p for p in store.get_all_patients() if p.patient_id.upper() == norm_id.upper()]
        if id_matches:
            return id_matches

    cleaned_lower = cleaned.lower()

    # Check for direct patient ID match
    id_matches = [p for p in store.get_all_patients() if p.patient_id.lower() == cleaned_lower]
    if id_matches:
        return id_matches

    # Check exact full name match first
    exact_name_matches = [p for p in store.get_all_patients() if p.name.lower() == cleaned_lower]
    if len(exact_name_matches) == 1:
        return exact_name_matches

    # Substring / token matching
    candidates = []
    for p in store.get_all_patients():
        p_name = p.name.lower()
        if cleaned_lower in p_name:
            candidates.append(p)
        else:
            # Check individual tokens (e.g. "Sharma" or "Priya")
            tokens = cleaned.split()
            if any(t in p_name.split() for t in tokens if len(t) > 2):
                if p not in candidates:
                    candidates.append(p)

    return candidates

def get_latest_report(
    patient_id: str,
    modality: Optional[str] = None,
    store: DataStore = data_store
) -> Optional[Report]:
    """
    Retrieves the most recent report for a patient, optionally filtered by modality.
    Sorts strictly by ISO date descending.
    """
    reports = [r for r in store.get_all_reports() if r.patient_id.lower() == patient_id.lower()]
    if modality:
        mod_clean = modality.strip().upper()
        reports = [r for r in reports if r.modality.upper() == mod_clean]

    if not reports:
        return None

    # Sort descending by date
    reports.sort(key=lambda r: r.date, reverse=True)
    return reports[0]

def list_reports(patient_id: str, store: DataStore = data_store) -> List[Report]:
    """
    Returns all reports for a patient, sorted by date descending.
    """
    reports = [r for r in store.get_all_reports() if r.patient_id.lower() == patient_id.lower()]
    reports.sort(key=lambda r: r.date, reverse=True)
    return reports

def get_report_evidence(report: Report) -> Dict[str, Any]:
    """
    Extracts explicit ground-truth evidence reference for auditability.
    """
    return {
        "report_id": report.report_id,
        "patient_id": report.patient_id,
        "modality": report.modality,
        "date": report.date,
        "findings": report.findings,
        "impression": report.impression,
        "evidence_snippet": report.evidence_snippet
    }
