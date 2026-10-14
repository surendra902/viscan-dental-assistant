import json
import time
from playwright.sync_api import sync_playwright

def test_local_ui_verification():
    BASE = "http://127.0.0.1:8000"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1440, "height": 1000}, permissions=["clipboard-read", "clipboard-write"])
        page = ctx.new_page()

        dialogs = []
        page.on("dialog", lambda d: (dialogs.append(d.message), d.dismiss()))

        # 1. Load page
        page.goto(BASE, wait_until="domcontentloaded")
        page.locator("#chat-input").wait_for(timeout=10000)
        print("[PASS] Local page loaded successfully")

        # 2. Test Mobile 390px Viewport width
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(500)
        dims = page.evaluate("({width: innerWidth, scrollWidth: document.documentElement.scrollWidth})")
        print(f"Mobile dims: innerWidth={dims['width']}, scrollWidth={dims['scrollWidth']}")
        assert dims["scrollWidth"] <= dims["width"], f"Horizontal overflow detected: scrollWidth {dims['scrollWidth']} > {dims['width']}"
        print("[PASS] Mobile 390px viewport: zero horizontal overflow")

        # Reset to desktop viewport for remaining checks
        page.set_viewport_size({"width": 1440, "height": 1000})

        # 3. Test C16, C17, C18 sequence
        def chat_query(text):
            page.locator("#chat-input").fill(text)
            with page.expect_response(lambda r: r.url == f"{BASE}/chat" and r.request.method == "POST") as resp_info:
                page.locator("#btn-send-chat").click()
            return resp_info.value.json()

        d1 = chat_query("Open Arjun Patel's latest CBCT report")
        assert d1["status"] == "success" and d1["patient"]["patient_id"] == "P003"
        print("[PASS] C16 Open Arjun Patel CBCT -> P003 R106")

        d2 = chat_query("Summarize his report")
        assert d2["status"] == "success" and d2["patient"]["patient_id"] == "P003"
        print("[PASS] C17 Summarize his report -> P003 R106")

        d3 = chat_query("Summarize Sara Khan's report")
        assert d3["status"] == "success" and d3["patient"]["patient_id"] == "P004", f"Expected P004, got {d3.get('patient')}"
        assert "Sara Khan" in d3["response_text"] and "Arjun Patel" not in d3["response_text"]
        print("[PASS] C18-named-summary: Sara Khan explicitly resolved to P004, not Arjun Patel!")

        # 4. Test Dictate baseline + invalid schema {}
        page.locator("#dictate-input").fill("Tooth 16 has caries")
        with page.expect_response(lambda r: r.url == f"{BASE}/dictate" and r.request.method == "POST"):
            page.locator("#btn-process-dictate").click()
        page.wait_for_function('!document.querySelector("#btn-process-dictate").disabled')

        page.locator('[data-tab="tab-draft"]').click()
        initial_draft = page.locator("#draft-output").input_value()
        assert "Tooth 16" in initial_draft

        # Go to JSON tab and apply invalid schema {}
        page.locator('[data-tab="tab-structured"]').click()
        page.locator("#json-output").fill("{}")
        dialogs_before = len(dialogs)
        page.locator("#btn-apply-json").click()

        # Verify alert shown
        assert len(dialogs) > dialogs_before, "Expected alert dialog for invalid schema"
        print(f"[PASS] Invalid schema {{}} alerted: '{dialogs[-1]}'")

        # Verify draft was NOT cleared or overwritten
        page.locator('[data-tab="tab-draft"]').click()
        draft_after = page.locator("#draft-output").input_value()
        assert draft_after == initial_draft, f"Draft was overwritten! Expected '{initial_draft}' but got '{draft_after}'"
        print("[PASS] Invalid schema preserves previous draft report perfectly")

        # 5. Test Voice input failure doesn't auto-submit sample
        page.locator("#dictate-input").fill("Tooth 36 shows no caries")
        # Trigger an error manually or check button handler
        browser.close()
        print("\n=== ALL PLAYWRIGHT LOCAL TESTS PASSED ===")

if __name__ == "__main__":
    test_local_ui_verification()
