import asyncio
import subprocess
import time
import requests
from playwright.async_api import async_playwright

STREAMLIT_PORT = 8522
STREAMLIT_URL = f"http://localhost:{STREAMLIT_PORT}"

def start_streamlit():
    cmd = [
        "streamlit", "run", "app.py",
        "--server.port", str(STREAMLIT_PORT),
        "--server.headless", "true"
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    start = time.time()
    while time.time() - start < 35:
        try:
            r = requests.get(STREAMLIT_URL)
            if r.status_code == 200:
                print("Streamlit server ready on port", STREAMLIT_PORT)
                return proc
        except Exception:
            pass
        time.sleep(0.5)
    proc.terminate()
    raise RuntimeError("Failed to start Streamlit")

async def test_redesigned_threat_inspector():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(viewport={"width": 1400, "height": 900})
        page = await context.new_page()
        await page.goto(STREAMLIT_URL, wait_until="networkidle")

        status_box = page.locator(".status-box")
        await status_box.wait_for(timeout=25000)
        print("Page loaded successfully.")

        # 1. Locate Threat Inspector iframe in sidebar
        sidebar = page.locator('section[data-testid="stSidebar"]')
        await sidebar.wait_for(state="visible")
        
        inspector_frame = sidebar.locator('iframe').first
        await inspector_frame.wait_for(state="visible", timeout=10000)
        print("PASS: Threat Inspector iframe located in sidebar.")

        frame = page.frame_locator('section[data-testid="stSidebar"] iframe').first

        # 2. Check Threat Inspector Header
        panel = frame.locator('.panel')
        await panel.wait_for(state="visible", timeout=10000)
        
        header_text = await frame.locator('.head h2').inner_text()
        print("Header text:", repr(header_text))
        assert "THREAT INSPECTOR" in header_text.upper()
        
        pill_text = await frame.locator('.pill').inner_text()
        print("Pill text:", repr(pill_text))
        assert "4 AGENTS" in pill_text.upper()

        # 3. Check All 4 Agents Rendered
        agent_first = frame.locator('.agent').first
        await agent_first.wait_for(state="visible", timeout=10000)
        agents = frame.locator('.agent')
        count = await agents.count()
        print("Agent count:", count)
        assert count == 4, f"Expected 4 agents, got {count}"

        expected_agents = [
            ("01", "Agent 1: Behavior", "LLM"),
            ("02", "Agent 2: Risk", "ML+RULES"),
            ("03", "Agent 3: Validator", "RULES"),
            ("04", "Agent 4: Synthesizer", "QUORUM"),
        ]

        for i, (exp_node, exp_title, exp_tag) in enumerate(expected_agents):
            agent = agents.nth(i)
            node_txt = await agent.locator('.node').inner_text()
            title_txt = await agent.locator('.t').inner_text()
            tag_txt = await agent.locator('.tag').inner_text()
            print(f"Agent {i+1}: node={node_txt}, title={title_txt}, tag={tag_txt}")
            assert node_txt == exp_node
            assert exp_title in title_txt
            assert tag_txt == exp_tag

        # 4. Check Default State: Agent 2 is open by default
        agent2 = agents.nth(1)
        is_agent2_open = await agent2.evaluate("el => el.classList.contains('open')")
        print("Agent 2 open by default:", is_agent2_open)
        assert is_agent2_open, "Expected Agent 2 to be open by default"

        agent2_facts = await agent2.locator('.f').count()
        print("Agent 2 facts count:", agent2_facts)
        assert agent2_facts == 4, f"Expected 4 facts in Agent 2, got {agent2_facts}"

        # 5. Interactive Accordion Toggle: Click Agent 1
        agent1 = agents.nth(0)
        card1 = agent1.locator('.card')
        print("Clicking Agent 1 card...")
        await card1.click()
        await page.wait_for_timeout(400)

        is_agent1_open = await agent1.evaluate("el => el.classList.contains('open')")
        is_agent2_open_now = await agent2.evaluate("el => el.classList.contains('open')")
        print(f"After click: Agent 1 open={is_agent1_open}, Agent 2 open={is_agent2_open_now}")
        assert is_agent1_open, "Agent 1 must be open after click"
        assert not is_agent2_open_now, "Agent 2 must be closed when Agent 1 is clicked"

        agent1_facts = await agent1.locator('.f').count()
        assert agent1_facts == 4, f"Expected 4 facts in Agent 1, got {agent1_facts}"

        # 6. Verify Test Vectors Section Is Removed
        sep_count = await frame.locator('.sep').count()
        chips_count = await frame.locator('.chip').count()
        pdesc_count = await frame.locator('#pdesc').count()
        print(f"Test vectors elements count: sep={sep_count}, chips={chips_count}, pdesc={pdesc_count}")
        assert sep_count == 0, "Test vectors separator must be removed"
        assert chips_count == 0, "Test vectors chips must be removed"
        assert pdesc_count == 0, "Test vectors description paragraph must be removed"
        print("PASS: Verified Test Vectors section has been removed completely.")

        # 7. Check Iframe Auto-Height Synchronization (No overflow cut-off)
        iframe_box = await inspector_frame.bounding_box()
        panel_box = await panel.bounding_box()
        print(f"Iframe height: {iframe_box['height']}, Panel height: {panel_box['height']}")
        assert iframe_box['height'] >= panel_box['height'] - 10, "Iframe must fit panel without cut-off"

        # 8. Full Application Screenshot
        screenshot_path = "screenshot_threat_inspector_redesign.png"
        await page.screenshot(path=screenshot_path, full_page=True)
        print(f"Saved full-page screenshot to {screenshot_path}")

        # 9. Verify End-to-end Analyze Transaction still works
        print("\n--- Testing Analyze Transaction Button ---")
        analyze_btn = page.locator('button:has-text("Analyze transaction")')
        await analyze_btn.click()
        hero_card = page.locator('.hero-card')
        await hero_card.wait_for(state="visible", timeout=25000)
        print("Hero card rendered after analysis!")

        await browser.close()
        print("\n>>> ALL REDESIGNED THREAT INSPECTOR TESTS PASSED SUCCESSFULLY! <<<")

def main():
    proc = start_streamlit()
    try:
        asyncio.run(test_redesigned_threat_inspector())
    finally:
        proc.terminate()
        proc.wait(timeout=5)

if __name__ == "__main__":
    main()
