import os
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

SCREENSHOTS_DIR = Path("docs/screenshots")
OUT_PDF = Path("docs/Viscan_Clinical_Demo_Walkthrough.pdf")

def build_pdf():
    doc = SimpleDocTemplate(
        str(OUT_PDF),
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "CoverTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=22,
        leading=26,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=6
    )

    subtitle_style = ParagraphStyle(
        "CoverSub",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#475569"),
        spaceAfter=12
    )

    h1_style = ParagraphStyle(
        "PageTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=17,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=3
    )

    badge_style = ParagraphStyle(
        "BadgeText",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#0369a1")
    )

    query_box_style = ParagraphStyle(
        "QueryText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#0f172a")
    )

    body_style = ParagraphStyle(
        "HumanBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#334155")
    )

    callout_style = ParagraphStyle(
        "CalloutText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#1e293b")
    )

    story = []

    # =========================================================================
    # PAGE 1: Engineering Overview & Limitations
    # =========================================================================
    story.append(Paragraph("Viscan Dental Assistant: Verification Walkthrough", title_style))

    meta_data = [
        [
            Paragraph("<b>Architecture:</b> Decoupled LLM Parser + Python Domain Validator", body_style),
            Paragraph("<b>Test Suite:</b> 37 passed (pytest tests/)", body_style)
        ],
        [
            Paragraph("<b>Live URL:</b> https://viscan-dental-assistant.onrender.com", body_style),
            Paragraph("<b>Model:</b> nvidia/nemotron-3.5-lightning:free via OpenRouter", body_style)
        ],
        [
            Paragraph("<b>Mock Data:</b> 6 synthetic patients, 13 synthetic reports in JSON", body_style),
            Paragraph("<b>Repo:</b> github.com/surendra902/viscan-dental-assistant", body_style)
        ]
    ]
    meta_table = Table(meta_data, colWidths=[270, 270])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#cbd5e1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 10))

    story.append(Paragraph("<b>Why I built this this way:</b>", ParagraphStyle("H2", parent=h1_style, fontSize=11, leading=14)))
    intro_p = (
        "General-purpose language models often invent tooth numbers or diagnoses when asked clinical questions. "
        "To avoid this, I split the pipeline into two parts: an LLM that only extracts entity slots (patient names, "
        "modalities, anatomical sites), and deterministic Python code that queries local data files and validates "
        "findings against a dental anatomy allowlist. The web interface has two workspaces: the left card handles "
        "report lookup and multi-turn chat memory, while the right card handles audio dictation and draft validation."
    )
    story.append(Paragraph(intro_p, body_style))
    story.append(Spacer(1, 8))

    # Limitations box right on page 1
    limits_data = [[
        Paragraph(
            "<b>Known Limitations & Scope:</b><br/>"
            "• <b>Synthetic dataset only:</b> Contains 6 mock patients and 13 reports. Not tested against hospital PACS/RIS databases.<br/>"
            "• <b>Not clinically validated:</b> Built as an engineering prototype for course evaluation, not for actual diagnostic use.<br/>"
            "• <b>Regex fallback edge cases:</b> Entity extraction relies on regex and fuzzy matching; unusual grammar or sentence structures can miss slots.<br/>"
            "• <b>Free-tier model latency:</b> OpenRouter free tier can experience latency spikes; the system falls back to local rules if the API times out.",
            callout_style
        )
    ]]
    limits_table = Table(limits_data, colWidths=[540])
    limits_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#fffbeb")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#fde68a")),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(limits_table)
    story.append(Spacer(1, 10))

    # Summary table
    index_data = [
        ["#", "Feature", "Input Prompt / Action", "What the System Does"],
        ["01", "Feature A", "Open Priya Sharma's latest OPG report", "Extracts name and modality; pulls report R101 with grounding snippet."],
        ["02", "Feature C", "Summarize her report", "Resolves pronoun 'her' to P001 from in-memory session history."],
        ["03", "Feature C", "when did she came to hospital", "Temporal query over active patient records; returns 3 visit dates."],
        ["04", "Feature C", "what about her CBCT?", "Modality switch for active patient; pulls 3D scan R103."],
        ["05", "Feature A", "Open Priya's latest OPG report", "Detects two matches (P001, P002); halts and asks doctor to clarify."],
        ["06", "Feature A", "Open Sara Khan's latest CBCT report", "Sara Khan has an IOPA but no CBCT; returns not_found without guessing."],
        ["07", "Feature B", "Lower right third molar is horizontally impacted", "Validates site and observation against dental dictionary; creates draft."],
        ["08", "Feature B", "Structured JSON Schema View", "Allows doctor to edit parsed JSON directly before committing."],
        ["09", "Feature B", "Patient has dragon teeth with quantum decay", "Rejects non-dental terms; sets confidence to 0.30 and adds warning banner."],
        ["10", "Safety", "show all patients & Arjun Patil typo", "Blocks bulk data dump; offers fuzzy suggestion for misspelled name."]
    ]
    index_table = Table(index_data, colWidths=[22, 58, 210, 250])
    index_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0284c7")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 8),
        ('BOTTOMPADDING', (0,0), (-1,0), 4),
        ('TOPPADDING', (0,0), (-1,0), 4),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#f8fafc")]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,1), (-1,-1), 7.5),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,1), (-1,-1), 3),
        ('BOTTOMPADDING', (0,1), (-1,-1), 3),
    ]))
    story.append(index_table)
    story.append(PageBreak())

    # =========================================================================
    # SCENARIOS 1 to 10
    # =========================================================================
    scenarios = [
        {
            "num": "01",
            "title": "Scenario 01: Exact Report Retrieval (Feature A)",
            "badge": "FEATURE A · REPORT RETRIEVAL",
            "query": "Open Priya Sharma's latest OPG report",
            "img": "scenario_01_report_retrieval.png",
            "text": (
                "<b>Input:</b> Doctor asks for Priya Sharma's latest OPG scan.<br/>"
                "<b>Execution:</b> The regex parser extracts patient name 'Priya Sharma' and modality 'OPG'. "
                "The function <code>find_patient()</code> returns ID P001. <code>get_latest_report(P001, 'OPG')</code> "
                "pulls record R101 (2026-01-15), which details an impacted tooth 48 and periapical lesion on tooth 36. "
                "The UI displays the text response and renders the bottom evidence card linking directly to R101."
            ),
            "status": "Response: HTTP 200 | JSON status: success | Matched: Priya Sharma (P001) -> Report R101"
        },
        {
            "num": "02",
            "title": "Scenario 02: Multi-Turn Pronoun Context (Feature C)",
            "badge": "FEATURE C · PRONOUN RESOLUTION",
            "query": "Summarize her report",
            "img": "scenario_02_context_pronoun_summary.png",
            "text": (
                "<b>Input:</b> Immediately following Scenario 1, doctor asks to summarize 'her' report.<br/>"
                "<b>Execution:</b> Because no name is supplied, the router checks <code>session.last_patient_id</code> (P001) "
                "and <code>session.last_report_id</code> (R101). It builds a 3-part summary (Indication, Key Findings, Impression) "
                "from the active report without prompting the user to re-enter patient details."
            ),
            "status": "Response: HTTP 200 | JSON status: success | Context: Priya Sharma (P001) retained from Turn 1"
        },
        {
            "num": "03",
            "title": "Scenario 03: Temporal Follow-Up Over Visit History (Feature C)",
            "badge": "FEATURE C · VISIT HISTORY RAG",
            "query": "when did she came to hospital",
            "img": "scenario_03_temporal_context_memory.png",
            "text": (
                "<b>Bug I hit and fixed here:</b> In an earlier test, typing 'when did she came to hospital' failed with "
                "<i>Patient 'when did she came to hospital' not found</i>. The name extractor did not strip question prefixes, "
                "so it treated the whole sentence as a patient name. I updated the router in <code>app/llm.py</code> to check for "
                "temporal keywords (when, visit, hospital) combined with pronouns before name extraction. It now queries the datastore "
                "for all reports under P001 and returns her recorded dates: 2026-02-01 (CBCT), 2026-01-15 (OPG), and 2025-06-10 (OPG)."
            ),
            "status": "Response: HTTP 200 | JSON status: success | Resolved: 3 historical visits returned for P001"
        },
        {
            "num": "04",
            "title": "Scenario 04: In-Context Modality Switch (Feature C)",
            "badge": "FEATURE C · MODALITY PIVOT",
            "query": "what about her CBCT?",
            "img": "scenario_04_modality_pivot_cbct.png",
            "text": (
                "<b>Input:</b> Doctor asks for 'her CBCT' in the active session.<br/>"
                "<b>Execution:</b> The router detects the modality switch keyword 'CBCT' while keeping Priya Sharma (P001) as the active patient. "
                "It queries <code>get_latest_report('P001', 'CBCT')</code> and returns R103 (2026-02-01), noting tooth 48's close contact with "
                "the inferior alveolar nerve canal. <code>session.last_report_id</code> is updated to R103."
            ),
            "status": "Response: HTTP 200 | JSON status: success | Active patient kept; report pivoted to R103 (CBCT)"
        },
        {
            "num": "05",
            "title": "Scenario 05: Ambiguity Guardrail (Feature A)",
            "badge": "FEATURE A · AMBIGUITY HANDLING",
            "query": "Open Priya's latest OPG report",
            "img": "scenario_05_ambiguity_guardrail.png",
            "text": (
                "<b>Input:</b> User provides only first name 'Priya'.<br/>"
                "<b>Design choice:</b> The datastore has two patients matching 'Priya': Priya Sharma (P001) and Priya Menon (P002). "
                "The system does not select a default or guess based on recency. It halts, returns application status <code>ambiguous</code>, "
                "and prints both candidate names and IDs. The user must provide the full name or ID to proceed."
            ),
            "status": "Response: HTTP 200 | JSON status: ambiguous | Candidates returned: P001, P002 (no record opened)"
        },
        {
            "num": "06",
            "title": "Scenario 06: Missing Modality Handling (Feature A)",
            "badge": "FEATURE A · MISSING RECORD",
            "query": "Open Sara Khan's latest CBCT report",
            "img": "scenario_06_missing_modality.png",
            "text": (
                "<b>Input:</b> User requests a CBCT for Sara Khan (P004).<br/>"
                "<b>Execution:</b> Sara Khan exists in <code>patients.json</code>, but only has an IOPA periapical record. "
                "Instead of generating mock findings or failing silently, the app returns: "
                "<i>'Found patient Sara Khan (P004), but no CBCT report was found in records.'</i>"
            ),
            "status": "Response: HTTP 200 | JSON status: not_found | Patient found, requested modality missing"
        },
        {
            "num": "07",
            "title": "Scenario 07: Clinical Dictation to Draft (Feature B)",
            "badge": "FEATURE B · DICTATION STRUCTURING",
            "query": "Lower right third molar is horizontally impacted",
            "img": "scenario_07_clinical_dictation_draft.png",
            "text": (
                "<b>Input:</b> Doctor dictates clinical observation into the Right Panel.<br/>"
                "<b>Execution:</b> The parser isolates anatomical site ('Lower right third molar') and observation ('horizontally impacted'). "
                "<code>app/validators.py</code> validates 'Lower right third molar' against FDI tooth 48 and confirms 'horizontally impacted' in "
                "the dental pathology dictionary. A draft report is compiled with the status line <code>requires_review: true</code>."
            ),
            "status": "Response: HTTP 200 | is_supported: true | confidence: 0.95 | requires_review: true"
        },
        {
            "num": "08",
            "title": "Scenario 08: Structured JSON View & Manual Edits (Feature B)",
            "badge": "FEATURE B · EDITABLE JSON PAYLOAD",
            "query": "Inspection of Structured JSON Tab",
            "img": "scenario_08_clinical_dictation_json.png",
            "text": (
                "<b>Human-in-the-loop workflow:</b> Selecting the 'Structured JSON' tab exposes the raw parsed array of "
                "<code>{anatomical_site, observation, confidence, is_supported}</code> objects. The textarea is editable. "
                "A clinician can correct a misheard tooth number or observation and click 'Apply Edits to Draft' to update the generated text "
                "before exporting."
            ),
            "status": "State: Frontend JSON editor active | Allows clinician overrides before saving"
        },
        {
            "num": "09",
            "title": "Scenario 09: Rejecting Fictitious Clinical Claims (Feature B)",
            "badge": "FEATURE B · DICTIONARY VALIDATION",
            "query": "Patient has dragon teeth with quantum decay",
            "img": "scenario_09_adversarial_interception_safety.png",
            "text": (
                "<b>Adversarial test:</b> Non-dental phrases were passed to test hallucination resistance.<br/>"
                "<b>Execution:</b> The terms 'dragon teeth' and 'quantum decay' fail allowlist validation in <code>app/validators.py</code>. "
                "The validator sets <code>is_supported: false</code>, drops confidence to 0.30, adds both terms to <code>unsupported_claims</code>, "
                "and inserts warning banners into the draft text. The 'Safety & Flags' tab highlights both unverified entities."
            ),
            "status": "Response: HTTP 200 | is_supported: false | confidence: 0.30 | flagged in unsupported_claims"
        },
        {
            "num": "10",
            "title": "Scenario 10: Bulk Dump Guard & Typo Suggestion",
            "badge": "SAFETY · BULK DUMP & SPELL CHECK",
            "query": "show all patients  &  Open Arjun Patil's latest OPG report",
            "img": "scenario_10_production_guardrails.png",
            "text": (
                "<b>Test 1 (Bulk data dump):</b> Querying 'show all patients' matches a regex filter in <code>app/llm.py</code>. "
                "The endpoint returns <code>guardrail_blocked</code>, refusing to print the full patient directory.<br/>"
                "<b>Test 2 (Typo check):</b> Querying 'Arjun Patil' checks known names with <code>difflib.get_close_matches</code>. "
                "It does not open Arjun Patel's record automatically; it returns <i>Patient 'Arjun Patil' not found. Did you mean 'Arjun Patel'?</i>"
            ),
            "status": "Bulk query blocked | Typo halted with suggestion (no automatic false-positive opening)"
        }
    ]

    for sc in scenarios:
        story.append(Paragraph(sc["title"], h1_style))
        story.append(Paragraph(sc["badge"], badge_style))
        story.append(Spacer(1, 4))

        # Query box
        q_table = Table([[Paragraph(f"<b>Query / Input:</b> <code>\"{sc['query']}\"</code>", query_box_style)]], colWidths=[540])
        q_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('LEFTPADDING', (0,0), (-1,-1), 6),
            ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(q_table)
        story.append(Spacer(1, 4))

        # Varied explanation
        story.append(Paragraph(sc["text"], body_style))
        story.append(Spacer(1, 4))

        # Screenshot
        img_path = SCREENSHOTS_DIR / sc["img"]
        if img_path.exists():
            img = Image(str(img_path), width=540, height=340)
            story.append(img)
        else:
            story.append(Paragraph(f"[Missing screenshot: {sc['img']}]", body_style))

        story.append(Spacer(1, 4))

        # Status note
        stat_table = Table([[Paragraph(f"<b>Verification:</b> {sc['status']}", callout_style)]], colWidths=[540])
        stat_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f1f5f9")),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#94a3b8")),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ('LEFTPADDING', (0,0), (-1,-1), 6),
            ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(stat_table)

        story.append(PageBreak())

    doc.build(story)
    print(f"Updated PDF generated successfully at: {OUT_PDF}")

if __name__ == "__main__":
    build_pdf()
