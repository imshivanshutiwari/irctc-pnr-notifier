"""
Automated Browser UI Verification Script for RailPulse PNR Dashboard Redesign
Tests Layer A (Compact PNR Overview Grid) and Layer B (Full PRS Ticket Modal Viewer)
"""
import sys
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def run_verification():
    sys.stdout.reconfigure(encoding='utf-8')
    opts = Options()
    opts.add_argument('--headless=new')
    opts.add_argument('--window-size=1440,1080')
    opts.add_argument('--disable-gpu')
    opts.add_argument('--no-sandbox')

    output_dir = Path("screenshots_verification")
    output_dir.mkdir(exist_ok=True)

    print("=== RailPulse PNR Dashboard UI Verification ===")
    driver = webdriver.Chrome(options=opts)
    try:
        url = "http://127.0.0.1:8000/"
        print(f"1. Loading URL: {url}")
        driver.get(url)

        # Wait for PNR overview cards to render
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "pnr-card")))
        time.sleep(1) # Allow CSS animations to settle

        # 0. Verify Cinematic Railway Backdrop Layer
        backdrop = driver.find_element(By.CLASS_NAME, "railway-backdrop")
        assert backdrop is not None, "railway-backdrop element must exist"
        bg_style = driver.execute_script("return window.getComputedStyle(arguments[0]).backgroundImage;", backdrop)
        pointer_events = driver.execute_script("return window.getComputedStyle(arguments[0]).pointerEvents;", backdrop)
        position = driver.execute_script("return window.getComputedStyle(arguments[0]).position;", backdrop)
        print(f"Backdrop Position: {position}")
        print(f"Backdrop Pointer Events: {pointer_events}")
        print(f"Backdrop Background Image: {bg_style[:80]}...")
        assert "railway-background.jpg" in bg_style, "Backdrop must load railway-background.jpg"
        assert position == "fixed", "Backdrop must be fixed in place"
        assert pointer_events == "none", "Backdrop must have pointer-events: none"

        # 1. Verify Header & Pill Badge
        title_el = driver.find_element(By.CLASS_NAME, "overview-brand-title")
        subtitle_el = driver.find_element(By.CLASS_NAME, "overview-subtitle")
        pill_el = driver.find_element(By.ID, "overview-pnr-count-pill")
        mode_el = driver.find_element(By.CLASS_NAME, "overview-mode-label")

        print(f"Header Title: {title_el.text}")
        print(f"Subtitle: {subtitle_el.text}")
        print(f"Pill Badge: {pill_el.text}")
        print(f"Mode Label: {mode_el.text}")

        assert "RailPulse" in title_el.text, "Title mismatch"
        assert "Your journey dashboard" in subtitle_el.text, "Subtitle mismatch"
        assert "PNRs tracked" in pill_el.text, "Pill badge mismatch"

        # 2. Verify Cards Grid
        cards = driver.find_elements(By.CLASS_NAME, "pnr-card")
        print(f"Rendered PNR Cards Count: {len(cards)}")
        assert len(cards) >= 1, "Expected at least 1 PNR card"

        for idx, card in enumerate(cards):
            label = card.find_element(By.CLASS_NAME, "pnr-label").text
            route = card.find_element(By.CLASS_NAME, "pnr-route").text
            status = card.find_element(By.CLASS_NAME, "pnr-current-status").text
            movement = card.find_element(By.CLASS_NAME, "pnr-movement-text").text
            btn = card.find_element(By.CLASS_NAME, "btn-view-ticket")
            print(f"  Card {idx + 1}: Label='{label}', Route='{route}', Status='{status}', Movement='{movement}', Button='{btn.text}'")

        # Capture Screenshot of Layer A: Compact Dashboard Overview with Cinematic Background
        screenshot1 = output_dir / "01_layer_a_overview_grid.png"
        driver.save_screenshot(str(screenshot1))
        print(f"Saved Layer A Screenshot to: {screenshot1}")

        # 3. Test Layer B: Click 'View ticket' on Card 1 to open Modal
        first_btn = cards[0].find_element(By.CLASS_NAME, "btn-view-ticket")
        first_pnr_text = cards[0].find_element(By.CLASS_NAME, "pnr-number-muted").text
        print(f"\n2. Clicking 'View ticket' for PNR {first_pnr_text}...")
        first_btn.click()
        time.sleep(1)

        # Verify modal is visible
        modal = driver.find_element(By.ID, "prs-ticket-modal")
        assert modal.is_displayed(), "Modal should be visible after clicking View ticket"

        modal_title = driver.find_element(By.ID, "modal-pnr-title").text
        modal_badge = driver.find_element(By.ID, "modal-pnr-badge").text
        print(f"Modal Opened: Title='{modal_title}', Badge='{modal_badge}'")
        assert first_pnr_text in modal_badge, f"Modal badge should match clicked PNR {first_pnr_text}"

        # Verify switcher tabs inside modal
        tabs = driver.find_elements(By.CLASS_NAME, "modal-tab-btn")
        print(f"Modal Switcher Tabs Count: {len(tabs)}")
        assert len(tabs) == len(cards), "Tab count should match card count"

        # Verify full PRS ticket is mounted inside modal viewport
        ticket_box = driver.find_element(By.CSS_SELECTOR, "#modal-ticket-viewport .ticket-box")
        assert ticket_box.is_displayed(), "Ticket box must be rendered in modal viewport"

        # Capture Screenshot of Layer B: Full PRS Ticket Modal
        screenshot2 = output_dir / "02_layer_b_prs_ticket_modal.png"
        driver.save_screenshot(str(screenshot2))
        print(f"Saved Layer B Modal Screenshot to: {screenshot2}")

        # 4. Test Tab Switching inside Modal
        if len(tabs) > 1:
            print("\n3. Testing tab switching to second PNR inside modal...")
            tabs[1].click()
            time.sleep(0.5)
            new_badge = driver.find_element(By.ID, "modal-pnr-badge").text
            print(f"Switched Tab Badge: {new_badge}")
            assert new_badge != modal_badge, "Badge should change on tab switch"

            screenshot3 = output_dir / "03_layer_b_switched_ticket.png"
            driver.save_screenshot(str(screenshot3))
            print(f"Saved Switched Tab Screenshot to: {screenshot3}")

        # 5. Test Closing Modal with Escape Key
        print("\n4. Pressing Escape key to dismiss modal...")
        webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()
        time.sleep(0.5)
        assert not modal.is_displayed(), "Modal should be hidden after pressing Escape"
        print("Modal successfully closed via Escape key!")

        # 6. Test Filtering
        print("\n5. Testing fleet filter tabs...")
        btn_prog = driver.find_element(By.XPATH, "//button[@data-filter='progressing']")
        btn_prog.click()
        time.sleep(0.5)
        visible_cards = [c for c in driver.find_elements(By.CLASS_NAME, "pnr-card") if c.is_displayed()]
        print(f"Visible cards under 'Progressing' filter: {len(visible_cards)}")

        btn_all = driver.find_element(By.XPATH, "//button[@data-filter='all']")
        btn_all.click()
        time.sleep(0.5)
        visible_all = [c for c in driver.find_elements(By.CLASS_NAME, "pnr-card") if c.is_displayed()]
        print(f"Visible cards under 'All' filter: {len(visible_all)}")
        assert len(visible_all) == len(cards), "All cards should be visible again under All filter"

        # 7. Test Mobile Viewport (Responsive & Background Positioning)
        print("\n6. Testing mobile viewport (390 x 844)...")
        driver.set_window_size(390, 844)
        time.sleep(1)
        mobile_screenshot = output_dir / "04_mobile_viewport_view.png"
        driver.save_screenshot(str(mobile_screenshot))
        print(f"Saved Mobile Screenshot to: {mobile_screenshot}")

        print("\n=== ALL BROWSER UI VERIFICATION TESTS PASSED SUCCESSFULLY! ===")
        return True
    finally:
        driver.quit()

if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1)
