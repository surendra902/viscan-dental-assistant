from typing import List, Optional, Dict, Any
from app.models import Patient, Report
from app.data_store import DataStore, data_store

def find_patient(name: str, store: DataStore = data_store) -> List[Patient]:
    """
    Search for patients by full or partial name, or patient ID.
    Returns 0, 1, or multiple matches (triggering disambiguation).
    """
    cleaned = name.strip().lower()
    cleaned = cleaned.strip(" \t\n\r.?!,;:")
    if not cleaned:
        return []

    # Check for direct patient ID match
    id_matches = [p for p in store.get_all_patients() if p.patient_id.lower() == cleaned]
    if id_matches:
        return id_matches

    # Check exact full name match first
    exact_name_matches = [p for p in store.get_all_patients() if p.name.lower() == cleaned]
    if len(exact_name_matches) == 1:
        return exact_name_matches

    # Substring / token matching
    candidates = []
    for p in store.get_all_patients():
        p_name = p.name.lower()
        if cleaned in p_name:
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
