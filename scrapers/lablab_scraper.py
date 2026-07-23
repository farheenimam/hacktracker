from bs4 import BeautifulSoup

STEALTH_INIT_SCRIPT = """
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
window.chrome = { runtime: {} };
"""

CHALLENGE_MARKERS = ["captcha", "verify you are human", "just a moment", "checking your browser", "attention required"]

def scrape_lablab():
    hackathons = []
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled"],
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                viewport={"width": 1366, "height": 900},
                locale="en-US",
                timezone_id="America/New_York",
                extra_http_headers={"Accept-Language": "en-US,en;q=0.9"},
            )
            context.add_init_script(STEALTH_INIT_SCRIPT)
            page = context.new_page()
            page.goto("https://lablab.ai/event", wait_until="domcontentloaded", timeout=40000)
            try:
                page.wait_for_selector("a[href^='/event/']", timeout=15000)
            except Exception:
                pass
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(2000)
            content = page.content()
            lowered = content.lower()
            if any(marker in lowered for marker in CHALLENGE_MARKERS):
                print("[lablab.ai] Blocked by a bot-challenge page (not a parsing issue)")
            soup = BeautifulSoup(content, "lxml")
            seen = set()
            for link in soup.select("a[href^='/event/']"):
                href = link.get("href","")
                if not href or href.rstrip("/") == "/event": continue
                full_url = f"https://lablab.ai{href}"
                if full_url in seen: continue
                seen.add(full_url)
                title_el = link.select_one("h2,h3,h4,[class*='title'],[class*='name']")
                title = title_el.get_text(strip=True) if title_el else link.get_text(strip=True)[:100]
                if not title or len(title) < 5: continue
                if any(w in title.lower() for w in ["home","about","blog","sign","login"]): continue
                status_el = link.select_one("[class*='status'],[class*='badge']")
                status_text = (status_el.get_text(strip=True) if status_el else "").lower()
                if any(w in status_text for w in ["ended","closed","finished"]): continue
                date_el = link.select_one("time,[class*='date'],[datetime]")
                deadline = (date_el.get("datetime") or date_el.get_text(strip=True)) if date_el else "TBD"
                img_el = link.select_one("img[src]")
                thumbnail = img_el.get("src","") if img_el else ""
                if thumbnail and thumbnail.startswith("/"): thumbnail = f"https://lablab.ai{thumbnail}"
                hackathons.append({"source":"lablab.ai","title":title,"url":full_url,"deadline":deadline,"prize":"See event page","thumbnail":thumbnail,"description":"AI hackathon on lablab.ai","status":"open"})
            browser.close()
    except ImportError:
        print("[lablab.ai] Playwright not installed")
    except Exception as e:
        print(f"[lablab.ai] Error: {e}")
    print(f"[lablab.ai] {len(hackathons)} events")
    return hackathons
