import re
from typing import List, Dict, Tuple, Any
from app.models import StructuredFinding

# Controlled Dental Vocabulary for Anatomical Sites
DENTAL_ANATOMY_KEYWORDS = {
    # Quadrants & Arches
    "lower right", "lower left", "upper right", "upper left",
    "mandible", "mandibular", "maxilla", "maxillary",
    "posterior", "anterior", "bilateral", "unilateral",
    # Tooth types & numbers
    "molar", "third molar", "wisdom tooth", "premolar", "bicuspid",
    "canine", "cuspid", "incisor", "central incisor", "lateral incisor",
    "tooth", "teeth", "dentition",
    # Specific anatomical structures
    "ramus", "condyle", "temporomandibular", "tmj", "alveolar bone",
    "alveolar crest", "root", "roots", "apex", "apical", "crown",
    "pulp", "pulp chamber", "periodontal ligament", "pdl",
    "inferior alveolar nerve", "ian canal", "mental foramen",
    "lingual plate", "buccal plate", "lingual cortex", "buccal cortex",
    "palate", "palatal", "occlusal", "mesial", "distal", "facial",
    "cervical", "furcation", "trabecular bone"
}

# Controlled Clinical Pathology / Observation Vocabulary
DENTAL_OBSERVATION_KEYWORDS = {
    "impacted", "impaction", "horizontally impacted", "vertically impacted",
    "mesioangular", "distoangular", "partially erupted", "unerupted",
    "caries", "decay", "cavity", "radiolucency", "radiopacity",
    "periapical lesion", "periodontitis", "bone loss", "horizontal bone loss",
    "vertical bone loss", "angular defect", "calculus", "plaque",
    "root resorption", "external resorption", "internal resorption",
    "fracture", "root fracture", "crown fracture", "crack",
    "cyst", "dentigerous cyst", "ameloblastoma", "odontogenic keratocyst",
    "osteolytic", "perforation", "cortical breach", "fenestration",
    "widened pdl", "widened periodontal ligament", "subluxation", "luxation",
    "overhanging restoration", "restoration", "filling", "defective restoration",
    "missing tooth", "missing teeth", "edentulous", "supernumerary",
    "deciduous", "retained deciduous", "contact", "displacement"
}

# Known Non-Dental / Fictitious / Unsupported Patterns
FICTITIOUS_PATTERNS = [
    r"dragon\s*teeth",
    r"quantum\s*decay",
    r"nano\s*cavity",
    r"vampire",
    r"adamantium",
    r"kryptonite",
    r"alien",
    r"cyborg"
]

# Uncertainty indicators in clinical text
UNCERTAINTY_INDICATORS = [
    "suggestive of", "possible", "probable", "appears", "suspected",
    "cannot rule out", "borderline", "questionable", "equivocal",
    "mild", "potential", "uncertain", "unclear", "investigate further"
]

def check_dental_site_validity(site_text: str) -> bool:
    """Verifies that an anatomical site refers to valid human dental anatomy."""
    site_lower = site_text.lower()
    for pattern in FICTITIOUS_PATTERNS:
        if re.search(pattern, site_lower):
            return False

    # Check for tooth numbering patterns (e.g., tooth 48, #16, 36)
    if re.search(r"\b(tooth|teeth|#)?\s*([1-4][1-8]|[5-8][1-5]|[1-9]|[12][0-9]|3[0-2])\b", site_lower):
        return True

    # Check against anatomical keywords
    return any(keyword in site_lower for keyword in DENTAL_ANATOMY_KEYWORDS)

def check_observation_validity(obs_text: str) -> bool:
    """Verifies that a clinical observation is a valid dental clinical finding."""
    obs_lower = obs_text.lower()
    for pattern in FICTITIOUS_PATTERNS:
        if re.search(pattern, obs_lower):
            return False

    return any(keyword in obs_lower for keyword in DENTAL_OBSERVATION_KEYWORDS)

def detect_uncertainty(text: str) -> List[str]:
    """Detects any explicit clinical uncertainty markers."""
    text_lower = text.lower()
    detected = []
    for marker in UNCERTAINTY_INDICATORS:
        if marker in text_lower:
            detected.append(f"Observation contains uncertainty marker '{marker}'; clinician confirmation advised.")
    return detected

def validate_clinical_dictation(
    raw_findings: List[Dict[str, Any]],
    raw_transcript: str
) -> Tuple[List[StructuredFinding], List[str], List[str], str]:
    """
    Business-rule validation layer (strictly separated from LLM generation).
    Enforces allowlist checks, flags unsupported claims, identifies uncertainties,
    and formats a clinician-review draft.
    """
    structured_findings: List[StructuredFinding] = []
    uncertainties: List[str] = []
    unsupported_claims: List[str] = []

    # Check transcript for known unsupported/fictitious concepts
    for pattern in FICTITIOUS_PATTERNS:
        match = re.search(pattern, raw_transcript, re.IGNORECASE)
        if match:
            claim_text = match.group(0)
            unsupported_claims.append(f"Unrecognized or non-standard clinical entity: '{claim_text}'.")
            uncertainties.append(f"High risk finding: '{claim_text}' is not a recognized dental clinical condition.")

    # Process each finding extracted from transcript
    for item in raw_findings:
        site = item.get("anatomical_site", "Unspecified site")
        obs = item.get("observation", "Unspecified observation")
        conf = float(item.get("confidence", 0.90))

        is_site_valid = check_dental_site_validity(site)
        is_obs_valid = check_observation_validity(obs)

        # Check uncertainty
        site_uncertainties = detect_uncertainty(site)
        obs_uncertainties = detect_uncertainty(obs)
        uncertainties.extend(site_uncertainties)
        uncertainties.extend(obs_uncertainties)

        if not is_site_valid or not is_obs_valid:
            is_supported = False
            unsupported_str = f"Finding '{obs}' at site '{site}' contains unsupported or unverified dental terminology."
            if unsupported_str not in unsupported_claims:
                unsupported_claims.append(unsupported_str)
            uncertainties.append(f"Unverified clinical claim: '{site} - {obs}' flagged for mandatory clinician review.")
            conf = min(conf, 0.30)
        else:
            is_supported = True

        structured_findings.append(
            StructuredFinding(
                anatomical_site=site,
                observation=obs,
                confidence=conf,
                is_supported=is_supported
            )
        )

    # Compile draft report text
    draft_lines = ["CLINICAL OBSERVATION REPORT (DRAFT - REQUIRES CLINICIAN REVIEW)", ""]
    draft_lines.append(f"Raw Dictation: \"{raw_transcript}\"")
    draft_lines.append("")
    draft_lines.append("Structured Observations:")

    for f in structured_findings:
        status_tag = "[VALIDATED]" if f.is_supported else "[UNSUPPORTED / CAUTION]"
        draft_lines.append(f" - {status_tag} Site: {f.anatomical_site} | Observation: {f.observation} (Confidence: {f.confidence:.2f})")

    if unsupported_claims:
        draft_lines.append("")
        draft_lines.append("Clinician Flags / Unsupported Claims:")
        for claim in unsupported_claims:
            draft_lines.append(f" * WARNING: {claim}")

    draft_lines.append("")
    draft_lines.append("Status: DRAFT - Mandatory clinician sign-off required prior to final diagnostic record.")

    draft_report = "\n".join(draft_lines)

    return structured_findings, uncertainties, unsupported_claims, draft_report
