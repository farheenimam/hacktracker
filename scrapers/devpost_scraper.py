import requests, time
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "https://devpost.com/hackathons",
}
def scrape_devpost():
    hackathons = []; seen = set()
    for page in range(1, 8):
        params = [("challenge_type[]","online"),("status[]","open"),("status[]","upcoming"),("order_by","deadline"),("page",str(page))]
        try:
            r = requests.get("https://devpost.com/hackathons.json", headers=HEADERS, params=params, timeout=15)
            r.raise_for_status(); data = r.json()
            items = data.get("hackathons", [])
            if not items: break
            for h in items:
                url = h.get("url","")
                if not url or url in seen: continue
                seen.add(url)
                status = h.get("open_state","")
                if status not in ("open","upcoming"): continue
                period = h.get("submission_period_dates","") or ""
                deadline = period.split(" - ")[-1].strip() if " - " in period else period
                hackathons.append({"source":"Devpost","title":h.get("title",""),"url":url,"deadline":deadline or "TBD","prize":h.get("prize_amount","N/A") or "N/A","thumbnail":h.get("thumbnail_url","") or "","description":h.get("tagline","") or "","status":status})
            meta = data.get("meta",{}); 
            if len(hackathons) >= meta.get("total_count",0): break
            time.sleep(0.4)
        except Exception as e:
            print(f"[Devpost] page {page}: {e}"); break
    print(f"[Devpost] {len(hackathons)} hackathons")
    return hackathons
