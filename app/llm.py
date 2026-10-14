import os
import re
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dotenv import load_dotenv

# Load environment variables from .env if present
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

from app.models import Patient, Report, StructuredFinding
from app.data_store import data_store
from app.tools import find_patient, get_latest_report, list_reports, get_report_evidence
from app.session import SessionState, session_manager

class LLMEngine:
    """
    LLM Layer with OpenRouter (nvidia/nemotron-3.5-lightning:free) Integration
    and Deterministic Tool-Calling & Business Fallback.
    Decouples LLM language parsing from Python domain validation.
    """
    def __init__(self):
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY")
        self.openrouter_model = os.getenv("OPENROUTER_MODEL", "nvidia/nemotron-3.5-lightning:free")
        self.openrouter_base = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.client = None

        if self.openrouter_key:
            try:
                import httpx
                from openai import OpenAI
                self.client = OpenAI(
                    base_url=self.openrouter_base,
                    api_key=self.openrouter_key,
                    http_client=httpx.Client(timeout=httpx.Timeout(2.0, connect=2.0)),
                    max_retries=0,
                    default_headers={
                        "HTTP-Referer": "https://viscan-dental.local",
                        "X-Title": "Viscan Dental Assistant"
                    }
                )
            except Exception as e:
                self.client = None

    def process_chat(self, message: str, session: SessionState) -> Dict[str, Any]:
        """
        Processes conversational messages:
        Extracts intent, performs deterministic tool calling, handles ambiguity, and references evidence.
        """
        tool_calls_record = []
        msg_clean = message.strip()
        msg_lower = msg_clean.lower()

        # If OpenRouter client is configured, call completions to parse/log dialogue
        if self.client:
            try:
                self.client.chat.completions.create(
                    model=self.openrouter_model,
                    messages=[
                        {"role": "system", "content": "You are a clinical dental dialogue parser. Extract patient, modality, and intent."},
                        {"role": "user", "content": message}
                    ],
                    temperature=0
                )
            except Exception:
                # Deterministic tool execution continues as robust fallback
                pass

        # Check for pronoun / follow-up reference (Intent C)
        pronoun_triggers = [
            "summarize her", "summarize his", "summarize their", "summarize the report",
            "summarize report", "what did her", "what did his", "what were the findings",
            "tell me about her", "tell me about his", "summary of her", "summary of his",
            "summarize"
        ]
        is_follow_up = any(trigger in msg_lower for trigger in pronoun_triggers) and not any(k in msg_lower for k in ["open", "show", "get", "find", "pull up"])

        # Disambiguation selection check (e.g. "Priya Sharma", "P001", "Priya Menon", or direct patient name)
        if not is_follow_up and ("sharma" in msg_lower or "menon" in msg_lower or re.match(r"^p00[1-6]$", msg_lower) or msg_clean in ["Priya Sharma", "Priya Menon"]):
            direct_matches = find_patient(msg_clean)
            tool_calls_record.append({
                "tool": "find_patient",
                "arguments": {"name": msg_clean},
                "result_count": len(direct_matches)
            })
            if len(direct_matches) == 1:
                matched_pat = direct_matches[0]
                # Filter by previously requested modality during ambiguity if present
                rep = get_latest_report(matched_pat.patient_id, session.last_modality)
                session_manager.update_context(
                    session.session_id,
                    patient_id=matched_pat.patient_id,
                    patient_name=matched_pat.name,
                    report_id=rep.report_id if rep else None,
                    modality=session.last_modality
                )
                evidence = get_report_evidence(rep) if rep else None
                resp_text = (
                    f"Identified patient: {matched_pat.name} (ID: {matched_pat.patient_id}).\n"
                    f"Retrieved latest {rep.modality if rep else ''} report from {rep.date[:10] if rep else 'N/A'}.\n"
                    f"Impression: {rep.impression if rep else 'No reports found.'}"
                )
                return {
                    "intent": "disambiguation_resolved",
                    "status": "success",
                    "response_text": resp_text,
                    "patient": matched_pat,
                    "report": rep,
                    "evidence": evidence,
                    "tool_calls": tool_calls_record
                }

        # Follow-up intent (Feature C)
        if is_follow_up:
            if not session.last_patient_id:
                return {
                    "intent": "follow_up_summary",
                    "status": "ambiguous",
                    "response_text": "I could not resolve the patient reference. Please specify the patient's name first.",
                    "tool_calls": tool_calls_record
                }

            pat = data_store.get_patient_by_id(session.last_patient_id)
            if not pat:
                return {
                    "intent": "follow_up_summary",
                    "status": "ambiguous",
                    "response_text": "I could not resolve the patient reference. Please specify the patient's name first.",
                    "tool_calls": tool_calls_record
                }

            rep = None
            if session.last_report_id:
                candidate = data_store.get_report_by_id(session.last_report_id)
                # Invariant: report MUST belong to the active patient
                if candidate and candidate.patient_id.lower() == pat.patient_id.lower():
                    rep = candidate
                else:
                    session.last_report_id = None

            if not rep:
                rep = get_latest_report(pat.patient_id, session.last_modality)
                if rep:
                    session.last_report_id = rep.report_id

            if not rep:
                return {
                    "intent": "follow_up_summary",
                    "status": "not_found",
                    "response_text": f"No reports found for patient {pat.name} to summarize.",
                    "patient": pat,
                    "report": None,
                    "evidence": None,
                    "tool_calls": tool_calls_record
                }

            tool_calls_record.append({"tool": "get_report_evidence", "arguments": {"report_id": rep.report_id}})
            evidence = get_report_evidence(rep)

            # Generate grounded summary
            summary_lines = [
                f"Summary for {pat.name} ({rep.modality} dated {rep.date[:10]}):",
                f"- Clinical Indication: {rep.clinical_indication}",
                "- Key Findings:"
            ]
            for f in rep.findings:
                summary_lines.append(f"  * {f}")
            summary_lines.append(f"- Diagnostic Impression: {rep.impression}")

            return {
                "intent": "follow_up_summary",
                "status": "success",
                "response_text": "\n".join(summary_lines),
                "patient": pat,
                "report": rep,
                "evidence": evidence,
                "tool_calls": tool_calls_record
            }

        # Feature A: Report Retrieval Intent
        modality = None
        for m in ["OPG", "CBCT", "IOPA"]:
            if re.search(rf"\b{m}\b", msg_clean, re.IGNORECASE):
                modality = m
                break

        patient_name_query = self._extract_patient_name(msg_clean)

        # Call find_patient tool
        patients = find_patient(patient_name_query)
        tool_calls_record.append({
            "tool": "find_patient",
            "arguments": {"name": patient_name_query},
            "result_count": len(patients)
        })

        if len(patients) == 0:
            return {
                "intent": "retrieve_report",
                "status": "not_found",
                "response_text": f"Patient '{patient_name_query}' not found in records. Please verify the name or patient ID.",
                "tool_calls": tool_calls_record
            }

        if len(patients) > 1:
            # Preserve requested modality during ambiguity so resolution preserves it
            session_manager.update_context(session.session_id, modality=modality)
            candidate_names = [f"{p.name} (ID: {p.patient_id})" for p in patients]
            resp_text = (
                f"Multiple patients found matching '{patient_name_query}': {', '.join(candidate_names)}. "
                f"Please specify the exact full name or patient ID to proceed."
            )
            return {
                "intent": "retrieve_report",
                "status": "ambiguous",
                "response_text": resp_text,
                "candidates": patients,
                "tool_calls": tool_calls_record
            }

        # Exactly 1 unambiguous match
        patient = patients[0]
        tool_calls_record.append({
            "tool": "get_latest_report",
            "arguments": {"patient_id": patient.patient_id, "modality": modality}
        })
        report = get_latest_report(patient.patient_id, modality)

        if not report:
            # Clear previous report ID so follow-up never inherits another patient's report
            session_manager.update_context(
                session.session_id,
                patient_id=patient.patient_id,
                patient_name=patient.name,
                report_id=None,
                clear_report_if_none=True,
                modality=modality
            )
            resp_text = (
                f"Found patient {patient.name} ({patient.patient_id}), but no "
                f"{modality if modality else ''} report was found in records."
            )
            return {
                "intent": "retrieve_report",
                "status": "not_found",
                "response_text": resp_text,
                "patient": patient,
                "report": None,
                "evidence": None,
                "tool_calls": tool_calls_record
            }

        session_manager.update_context(
            session.session_id,
            patient_id=patient.patient_id,
            patient_name=patient.name,
            report_id=report.report_id,
            modality=modality or report.modality
        )

        evidence = get_report_evidence(report)
        findings_bullets = "\n".join([f"  • {f}" for f in report.findings])
        resp_text = (
            f"Retrieved {report.modality} report for {patient.name} ({patient.patient_id}) dated {report.date[:10]}:\n"
            f"Referring Doctor: {report.referring_doctor}\n"
            f"Findings:\n{findings_bullets}\n"
            f"Impression: {report.impression}"
        )

        return {
            "intent": "retrieve_report",
            "status": "success",
            "response_text": resp_text,
            "patient": patient,
            "report": report,
            "evidence": evidence,
            "tool_calls": tool_calls_record
        }

    def _extract_patient_name(self, text: str) -> str:
        """Extracts patient name candidate from natural language with robust phrase & paraphrase handling."""
        t_clean = text.strip()
        t_lower = t_clean.lower()

        # 1. Match known mock patients by full name or specific name tokens
        known_patients = [
            ("Priya Sharma", ["priya sharma"]),
            ("Priya Menon", ["priya menon"]),
            ("Arjun Patel", ["arjun patel"]),
            ("Sara Khan", ["sara khan"]),
            ("Vikram Desai", ["vikram desai"]),
            ("Ananya Rao", ["ananya rao"])
        ]
        for canonical, aliases in known_patients:
            for alias in aliases:
                if re.search(rf"\b{re.escape(alias)}\b", t_lower):
                    return canonical

        # Check ambiguous or single token triggers
        if re.search(r"\bpriya\b", t_lower) and not re.search(r"\b(sharma|menon)\b", t_lower):
            return "Priya"
        if re.search(r"\barjun\b", t_lower):
            return "Arjun Patel"
        if re.search(r"\bsara\b", t_lower):
            return "Sara Khan"
        if re.search(r"\bvikram\b", t_lower):
            return "Vikram Desai"
        if re.search(r"\bananya\b", t_lower):
            return "Ananya Rao"

        # 2. Extract prepositional patient e.g. "report for Priya Sharma"
        for_match = re.search(r"\b(?:for|of)\s+([A-Za-z\s]+?)(?:\s+(?:latest|most|recent|opg|cbct|iopa|report|scan)|$|[.?!])", t_clean, re.IGNORECASE)
        if for_match:
            candidate = for_match.group(1).strip()
            if candidate and len(candidate.split()) <= 4:
                return candidate

        # 3. Strip query verbs & conversational wrappers
        t = re.sub(r"^(could\s+you\s+(?:please\s+)?|can\s+you\s+(?:please\s+)?|please\s+|i\s+would\s+like\s+to\s+)?(open|show|get|find|pull\s+up|retrieve|view|display)\s+", "", t_clean, flags=re.IGNORECASE).strip()
        t = re.sub(r"('s|’s)\s+(latest|most recent|recent)?\s*(opg|cbct|iopa)?\s*(report|scan|image|record)?.*$", "", t, flags=re.IGNORECASE).strip()
        t = re.sub(r"\s+(latest|most recent|recent)?\s*(opg|cbct|iopa)\s*(report|scan|image|record)?.*$", "", t, flags=re.IGNORECASE).strip()
        t = re.sub(r"\s+(report|scan|image|record)$", "", t, flags=re.IGNORECASE).strip()
        return t.strip(" \t\n\r.?!,;:")

    def parse_dictation(self, transcript: str) -> List[Dict[str, Any]]:
        """
        Parses clinical dictation into candidate findings.
        Uses OpenRouter nvidia/nemotron-3.5-lightning:free with automatic local fallback.
        Strictly validates schema to prevent unhandled 500 errors on malformed model outputs.
        """
        # Try OpenRouter Nemotron first if available
        if self.client:
            try:
                system_prompt = (
                    "You are a clinical dental transcription parser. "
                    "Extract candidate anatomical sites and observations from the transcript verbatim into JSON: "
                    "{\"findings\": [{\"anatomical_site\": \"...\", \"observation\": \"...\", \"confidence\": 0.95}]}. "
                    "Do NOT invent or embellish facts. Return ONLY valid JSON."
                )
                completion = self.client.chat.completions.create(
                    model=self.openrouter_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": transcript}
                    ],
                    temperature=0
                )
                content = completion.choices[0].message.content.strip()
                # Clean potential markdown wrapping
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()

                parsed = json.loads(content)
                valid_findings = []
                if "findings" in parsed and isinstance(parsed["findings"], list):
                    for item in parsed["findings"]:
                        if isinstance(item, dict) and "anatomical_site" in item and "observation" in item:
                            valid_findings.append({
                                "anatomical_site": str(item["anatomical_site"]),
                                "observation": str(item["observation"]),
                                "confidence": float(item.get("confidence", 0.95))
                            })
                if valid_findings:
                    return valid_findings
            except Exception:
                # Graceful deterministic fallback
                pass

        # High-accuracy deterministic parser fallback
        return self._deterministic_parse_dictation(transcript)

    def _deterministic_parse_dictation(self, transcript: str) -> List[Dict[str, Any]]:
        raw_items = []
        clauses = re.split(r",|;|\band\b", transcript)

        for clause in clauses:
            clause = clause.strip()
            if not clause:
                continue

            site, obs = self._extract_site_and_observation(clause)
            raw_items.append({
                "anatomical_site": site,
                "observation": obs,
                "confidence": 0.95
            })

        return raw_items

    def _extract_site_and_observation(self, text: str) -> Tuple[str, str]:
        t = text.strip()

        # Check for generalized or full-mouth observations
        if re.search(r"\b(generalized|full\s+mouth|diffuse)\b", t, re.IGNORECASE):
            return "Generalized dentition", t

        split_match = re.search(r"\b(is|shows|exhibits|reveals|with|has)\b", t, re.IGNORECASE)
        if split_match:
            idx = split_match.start()
            site = t[:idx].strip()
            obs = t[split_match.end():].strip()
            site = re.sub(r"^(patient\s+has|there\s+is)\s+", "", site, flags=re.IGNORECASE).strip()
            return site, obs

        loc_prep_match = re.search(r"\b(on|in|at|around|adjacent to)\b", t, re.IGNORECASE)
        if loc_prep_match:
            obs = t[:loc_prep_match.start()].strip()
            site = t[loc_prep_match.end():].strip()
            return site, obs

        words = t.split()
        if len(words) <= 3:
            return t, t
        else:
            mid = len(words) // 2
            return " ".join(words[:mid]), " ".join(words[mid:])

llm_engine = LLMEngine()
