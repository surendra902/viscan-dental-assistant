import json
from pathlib import Path
from typing import List, Optional
from app.models import Patient, Report

DATA_DIR = Path(__file__).parent.parent / "data"

class DataStore:
    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or DATA_DIR
        self._patients: List[Patient] = []
        self._reports: List[Report] = []
        self.reload()

    def reload(self):
        patients_file = self.data_dir / "patients.json"
        reports_file = self.data_dir / "reports.json"

        if patients_file.exists():
            with open(patients_file, "r", encoding="utf-8") as f:
                raw_patients = json.load(f)
                self._patients = [Patient(**p) for p in raw_patients]
        else:
            self._patients = []

        if reports_file.exists():
            with open(reports_file, "r", encoding="utf-8") as f:
                raw_reports = json.load(f)
                self._reports = [Report(**r) for r in raw_reports]
        else:
            self._reports = []

    def get_all_patients(self) -> List[Patient]:
        return self._patients

    def get_all_reports(self) -> List[Report]:
        return self._reports

    def get_patient_by_id(self, patient_id: str) -> Optional[Patient]:
        for p in self._patients:
            if p.patient_id.lower() == patient_id.lower():
                return p
        return None

    def get_report_by_id(self, report_id: str) -> Optional[Report]:
        for r in self._reports:
            if r.report_id.lower() == report_id.lower():
                return r
        return None

# Singleton instance for standard app usage
data_store = DataStore()
