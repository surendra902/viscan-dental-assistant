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
    r"cyborg",
    r"intergalactic",
    r"moon\s*crystals?",
    r"magic",
    r"cosmic",
    r"astral",
    r"zombie"
]

# Uncertainty indicators in clinical text
UNCERTAINTY_INDICATORS = [
    "suggestive of", "possible", "probable", "appears", "suspected",
    "cannot rule out", "borderline", "questionable", "equivocal",
    "mild", "potential", "uncertain", "unclear", "investigate further", "rule out"
]

# Valid human dental tooth numbering systems
VALID_DENTAL_TOOTH_NUMBERS = (
    set(range(1, 33)) | # Universal permanent 1-32
    {11, 12, 13, 14, 15, 16, 17, 18,
     21, 22, 23, 24, 25, 26, 27, 28,
     31, 32, 33, 34, 35, 36, 37, 38,
     41, 42, 43, 44, 45, 46, 47, 48} | # FDI permanent quadrants 1-4
    {51, 52, 53, 54, 55,
     61, 62, 63, 64, 65,
     71, 72, 73, 74, 75,
     81, 82, 83, 84, 85} # FDI primary (deciduous) quadrants 5-8
)

def check_dental_site_validity(site_text: str) -> bool:
    """Verifies that an anatomical site refers to valid human dental anatomy."""
    site_lower = site_text.lower().strip()
    for pattern in FICTITIOUS_PATTERNS:
        if re.search(pattern, site_lower):
            return False

    # Check for explicit tooth numbers (e.g. tooth 99, tooth 16, #48)
    digits = re.findall(r"\b\d+\b", site_lower)
    if digits:
        for d in digits:
            num = int(d)
            if num not in VALID_DENTAL_TOOTH_NUMBERS:
                return False
        return True

    # Check against anatomical keywords
    return any(keyword in site_lower for keyword in DENTAL_ANATOMY_KEYWORDS)

def check_observation_validity(obs_text: str) -> bool:
    """Verifies that a clinical observation is a valid dental clinical finding."""
    obs_lower = obs_text.lower().strip()
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

LATERALITY_KEYWORDS = {
    "left", "right", "bilateral", "unilateral",
    "upper", "lower", "maxilla", "maxillary", "mandible", "mandibular",
    "anterior", "posterior"
}

def extract_clauses(text: str) -> List[str]:
    """Split transcript into semantic clauses, preserving punctuation boundaries."""
    raw_clauses = re.split(r"[;]|\band\b|[,]", text, flags=re.IGNORECASE)
    clauses = [c.strip() for c in raw_clauses if c.strip()]
    return clauses if clauses else [text.strip()]

def has_negation(text: str) -> bool:
    """Detects presence of clinical negation tokens."""
    t = text.lower()
    return any(re.search(rf"\b{term}\b", t) for term in ["no", "not", "without", "absent", "denies", "neither"])

def check_transcript_grounding(site: str, obs: str, raw_transcript: str) -> Tuple[bool, str]:
    """
    Verifies that extracted anatomical site and observation have lexical and semantic grounding
    in the source dictation to prevent ungrounded LLM hallucinations, laterality shifts,
    negation removal, pathology embellishment, and cross-site reassignments.
    """
    raw_lower = raw_transcript.lower()
    site_lower = site.lower().strip()
    obs_lower = obs.lower().strip()

    # 1. Whole-token tooth number check: If site specifies a tooth number, that exact token MUST be in the transcript
    site_digits = re.findall(r"\b\d+\b", site_lower)
    for digit in site_digits:
        if not re.search(rf"\b{digit}\b", raw_lower):
            return False, f"Extracted tooth number '{digit}' was not found in source dictation."

    # 2. Check laterality descriptors: Any laterality term in site MUST exist in raw dictation without contradiction
    for lat in LATERALITY_KEYWORDS:
        if re.search(rf"\b{lat}\b", site_lower) and not re.search(rf"\b{lat}\b", raw_lower):
            return False, f"Laterality descriptor '{lat}' in site '{site}' contradicts source dictation."

    # 3. Check pathology embellishment: Any clinical pathology term in observation MUST appear in source
    for path in DENTAL_OBSERVATION_KEYWORDS:
        # Check if a substantive multi-word or single-word pathology term is in candidate obs
        if re.search(rf"\b{re.escape(path)}\b", obs_lower) and not re.search(rf"\b{re.escape(path)}\b", raw_lower):
            # Check individual key words of the pathology
            path_words = [w for w in re.findall(r"\b[a-z]{4,}\b", path) if w not in {"with", "some", "mild", "loss"}]
            if any(re.search(rf"\b{re.escape(pw)}\b", obs_lower) and not re.search(rf"\b{re.escape(pw)}\b", raw_lower) for pw in path_words):
                return False, f"Pathology '{path}' in observation '{obs}' was not mentioned in source dictation."

    # 4. Check negation alignment:
    obs_negated = has_negation(obs_lower)
    raw_negated = has_negation(raw_lower)

    # 5. Clause-level binding: Finding (site + observation) must be grounded in the same clause/span
    clauses = extract_clauses(raw_transcript)
    matched_clause = None

    distinct_sites_count = 0
    active_site_clause = None

    for idx, clause in enumerate(clauses):
        c_lower = clause.lower()
        has_new_tooth = bool(re.search(r"\b\d+\b", c_lower))
        has_new_laterality = any(lat in c_lower for lat in ["upper", "lower", "maxillary", "mandibular", "right", "left"])
        has_generalized = any(g in c_lower for g in ["generalized", "diffuse", "full mouth"])

        if has_new_tooth or has_new_laterality or has_generalized or idx == 0:
            distinct_sites_count += 1

        # Check if candidate site matches this clause (or inherited clause if continuation)
        site_in_clause = False
        if "generalized" in site_lower and has_generalized:
            site_in_clause = True
        elif site_digits:
            site_in_clause = all(re.search(rf"\b{d}\b", c_lower) for d in site_digits)
        else:
            site_tokens = [w for w in re.findall(r"\b[a-z]{3,}\b", site_lower) if w not in {"tooth", "teeth", "site", "area"}]
            site_in_clause = all(w in c_lower for w in site_tokens) if site_tokens else True

        if not site_in_clause and not (has_new_tooth or has_new_laterality or has_generalized) and active_site_clause:
            site_in_clause = True

        if site_in_clause:
            active_site_clause = clause
            obs_tokens = [w for w in re.findall(r"\b[a-z]{3,}\b", obs_lower) if w not in {"shows", "with", "there", "have", "some", "mild", "deep", "has", "and"}]
            if any(w in c_lower for w in obs_tokens):
                matched_clause = clause
                break
        else:
            if has_new_tooth or has_new_laterality or has_generalized:
                active_site_clause = None

    # If transcript has multiple distinct sites across clauses, ensure site and obs co-occur
    if len(clauses) > 1 and distinct_sites_count > 1:
        if not matched_clause:
            return False, f"Finding '{obs}' was reassigned to '{site}' across different clauses in source dictation."

    # Verify negation against the matched clause (or raw transcript)
    target_text = matched_clause.lower() if matched_clause else raw_lower
    clause_negated = has_negation(target_text)

    if clause_negated and not obs_negated:
        return False, f"Observation '{obs}' removes clinical negation present in source ('{target_text}')."
    if obs_negated and not raw_negated:
        return False, f"Observation '{obs}' invents clinical negation not present in source."

    # 6. Basic site and obs grounding
    if site_digits:
        for digit in site_digits:
            if not re.search(rf"\b{digit}\b", raw_lower):
                return False, f"Extracted tooth number '{digit}' not found in source."
    elif "generalized" not in site_lower:
        site_words = [w for w in re.findall(r"\b[a-z]{3,}\b", site_lower) if w not in {"tooth", "teeth", "site", "area", "region"}]
        if site_words and not any(w in raw_lower for w in site_words):
            return False, f"Site '{site}' not grounded in source."

    obs_words = [w for w in re.findall(r"\b[a-z]{3,}\b", obs_lower) if w not in {"shows", "with", "there", "have", "some", "mild", "deep"}]
    if obs_words and not any(w in raw_lower for w in obs_words):
        return False, f"Observation '{obs}' has no textual grounding."

    return True, ""

def validate_clinical_dictation(
    raw_findings: List[Dict[str, Any]],
    raw_transcript: str
) -> Tuple[List[StructuredFinding], List[str], List[str], str]:
    """
    Business-rule validation layer (strictly separated from LLM generation).
    Enforces allowlist checks, transcript grounding, flags unsupported claims,
    identifies uncertainties, and formats a clinician-review draft.
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

    # Preserve any explicit uncertainty markers directly from the raw clinician dictation
    transcript_uncertainties = detect_uncertainty(raw_transcript)
    for u in transcript_uncertainties:
        if u not in uncertainties:
            uncertainties.append(u)

    # Process each finding extracted from transcript
    for item in raw_findings:
        if not isinstance(item, dict):
            continue

        site = str(item.get("anatomical_site", "Unspecified site"))
        obs = str(item.get("observation", "Unspecified observation"))
        conf = float(item.get("confidence", 0.90))

        is_site_valid = check_dental_site_validity(site)
        is_obs_valid = check_observation_validity(obs)
        is_grounded, ungrounded_reason = check_transcript_grounding(site, obs, raw_transcript)

        # Check uncertainty in generated fields
        site_uncertainties = detect_uncertainty(site)
        obs_uncertainties = detect_uncertainty(obs)
        for u in site_uncertainties + obs_uncertainties:
            if u not in uncertainties:
                uncertainties.append(u)

        if not is_site_valid or not is_obs_valid or not is_grounded:
            is_supported = False
            if not is_grounded:
                unsupported_claims.append(f"Ungrounded clinical candidate: {ungrounded_reason}")
                uncertainties.append(f"Model invention caution: '{site} - {obs}' lacks source transcript evidence.")
            else:
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
