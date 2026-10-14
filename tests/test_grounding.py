import pytest
from app.validators import check_transcript_grounding

@pytest.mark.parametrize("label,transcript,site,obs,expected", [
    # 5 semantic defect witnesses: must be False
    ('negation', 'Tooth 16 has no caries', 'Tooth 16', 'caries', False),
    ('laterality', 'Lower right third molar is horizontally impacted', 'Lower left third molar', 'horizontally impacted', False),
    ('reassignment', 'Tooth 16 has caries and tooth 48 is horizontally impacted', 'Tooth 48', 'caries', False),
    ('embellishment', 'Tooth 16 has caries', 'Tooth 16', 'caries and root fracture', False),
    ('tooth_substring', 'Tooth 16 has caries', 'Tooth 6', 'caries', False),
    # 3 faithful controls: must be True
    ('control1', 'Tooth 16 has caries', 'Tooth 16', 'caries', True),
    ('control2', 'Tooth 16 has no caries', 'Tooth 16', 'no caries', True),
    ('control3', 'Lower right third molar is horizontally impacted', 'Lower right third molar', 'horizontally impacted', True),
    # Additional complex / real-world cases
    ('complex_clause1', 'Deep occlusal caries on tooth 16 and generalized moderate horizontal bone loss', 'tooth 16', 'Deep occlusal caries', True),
    ('complex_clause2', 'Deep occlusal caries on tooth 16 and generalized moderate horizontal bone loss', 'Generalized dentition', 'generalized moderate horizontal bone loss', True),
    ('negated_radiolucency', 'Tooth 36 shows no periapical radiolucency', 'Tooth 36', 'no periapical radiolucency', True),
    ('negated_impacted', 'Lower right third molar is not horizontally impacted', 'Lower right third molar', 'not horizontally impacted', True),
    ('possible_radiolucency', 'Tooth 36 shows possible periapical radiolucency', 'Tooth 36', 'possible periapical radiolucency', True),
    ('continuation_clause', 'Tooth 16 has deep caries and shows periapical lesion', 'Tooth 16', 'periapical lesion', True),
    ('multi_quadrant_reassign', 'Upper right quadrant has calculus and lower left quadrant has bone loss', 'lower left quadrant', 'calculus', False),
])
def test_semantic_grounding_cases(label, transcript, site, obs, expected):
    valid, reason = check_transcript_grounding(site, obs, transcript)
    assert valid == expected, f"Failed for {label}: got valid={valid}, expected={expected}. Reason: {reason}"
