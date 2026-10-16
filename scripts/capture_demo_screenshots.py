import os
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT_DIR = Path("docs/screenshots")
OUT_DIR.mkdir(parents=True, exist_ok=True)

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 920})
        page = context.new_page()
        page.goto("http://127.0.0.1:8000")
        page.wait_for_load_state("networkidle")
        time.sleep(1)

        def send_chat(msg, delay=0.8):
            page.fill("#chat-input", msg)
            page.click("#btn-send-chat")
            time.sleep(delay)
            page.wait_for_load_state("networkidle")
            time.sleep(0.5)

        def clear_chat():
            page.click("#btn-clear-chat")
            time.sleep(0.4)

        def run_dictate(text, delay=0.8):
            page.fill("#dictate-input", text)
            page.click("#btn-process-dictate")
            time.sleep(delay)
            page.wait_for_load_state("networkidle")
            time.sleep(0.5)

        # ---------------------------------------------------------
        # Scenario 1: Report Retrieval & Grounding (Feature A)
        # ---------------------------------------------------------
        print("Capturing Scenario 1: Report Retrieval...")
        send_chat("Open Priya Sharma's latest OPG report")
        page.screenshot(path=str(OUT_DIR / "scenario_01_report_retrieval.png"))

        # ---------------------------------------------------------
        # Scenario 2: Context Pronoun Follow-Up (Feature C)
        # ---------------------------------------------------------
        print("Capturing Scenario 2: Context Pronoun Follow-up...")
        send_chat("Summarize her report")
        page.screenshot(path=str(OUT_DIR / "scenario_02_context_pronoun_summary.png"))

        # ---------------------------------------------------------
        # Scenario 3: Temporal RAG / Visit History (Feature C)
        # ---------------------------------------------------------
        print("Capturing Scenario 3: Temporal Context Query...")
        send_chat("when did she came to hospital")
        page.screenshot(path=str(OUT_DIR / "scenario_03_temporal_context_memory.png"))

        # ---------------------------------------------------------
        # Scenario 4: Modality Pivot Follow-Up (Feature C)
        # ---------------------------------------------------------
        print("Capturing Scenario 4: Modality Pivot...")
        send_chat("what about her CBCT?")
        page.screenshot(path=str(OUT_DIR / "scenario_04_modality_pivot_cbct.png"))

        # ---------------------------------------------------------
        # Scenario 5: Ambiguity Guardrail (Feature A)
        # ---------------------------------------------------------
        print("Capturing Scenario 5: Ambiguity Handling...")
        clear_chat()
        send_chat("Open Priya's latest OPG report")
        page.screenshot(path=str(OUT_DIR / "scenario_05_ambiguity_guardrail.png"))

        # ---------------------------------------------------------
        # Scenario 6: Missing Modality Non-Hallucination (Feature A)
        # ---------------------------------------------------------
        print("Capturing Scenario 6: Missing Modality...")
        clear_chat()
        send_chat("Open Sara Khan's latest CBCT report")
        page.screenshot(path=str(OUT_DIR / "scenario_06_missing_modality.png"))

        # ---------------------------------------------------------
        # Scenario 7: Valid Clinical Dictation (Feature B)
        # ---------------------------------------------------------
        print("Capturing Scenario 7: Clinical Dictation...")
        run_dictate("Lower right third molar is horizontally impacted")
        # Ensure Draft tab is active
        page.click('.tab-link[data-tab="tab-draft"]')
        time.sleep(0.3)
        page.screenshot(path=str(OUT_DIR / "scenario_07_clinical_dictation_draft.png"))

        # ---------------------------------------------------------
        # Scenario 8: Structured JSON View (Feature B)
        # ---------------------------------------------------------
        print("Capturing Scenario 8: Dictation Structured JSON...")
        page.click('.tab-link[data-tab="tab-structured"]')
        time.sleep(0.3)
        page.screenshot(path=str(OUT_DIR / "scenario_08_clinical_dictation_json.png"))

        # ---------------------------------------------------------
        # Scenario 9: Adversarial / Fictitious Claim Interception (Feature B)
        # ---------------------------------------------------------
        print("Capturing Scenario 9: Adversarial Claim Interception...")
        run_dictate("Patient has dragon teeth with quantum decay")
        page.click('.tab-link[data-tab="tab-safety"]')
        time.sleep(0.3)
        page.screenshot(path=str(OUT_DIR / "scenario_09_adversarial_interception_safety.png"))

        # ---------------------------------------------------------
        # Scenario 10: Production Security & Spell Guardrails
        # ---------------------------------------------------------
        print("Capturing Scenario 10: Security & Typo Guardrail...")
        clear_chat()
        send_chat("show all patients")
        send_chat("Open Arjun Patil's latest OPG report")
        page.screenshot(path=str(OUT_DIR / "scenario_10_production_guardrails.png"))

        browser.close()
        print("All 10 scenarios captured successfully!")

if __name__ == "__main__":
    run()
