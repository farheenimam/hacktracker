import requests, time, os
HEADERS = {"User-Agent":"HackTracker/2.0","Accept":"application/json"}
API_KEY = os.getenv("HACKEREARTH_API_KEY","")
def scrape_hackerearth():
    hackathons = []; seen = set()
    for status in ["ONGOING","UPCOMING"]:
        params = {"type":"HACKATHON","status":status,"offset":0}
        if API_KEY: params["client_secret"] = API_KEY
        while True:
            try:
                r = requests.get("https://www.hackerearth.com/api/v2/challenges/",headers=HEADERS,params=params,timeout=15)
                r.raise_for_status(); data = r.json(); items = data.get("results",[])
                if not items: break
                for h in items:
                    url = h.get("challenge_url") or h.get("url","")
                    if not url or url in seen: continue
                    seen.add(url)
                    hackathons.append({"source":"HackerEarth","title":h.get("title") or h.get("name",""),"url":url,"deadline":(h.get("end_utc") or "")[:10] or "TBD","prize":h.get("prize_in_cash","") or "See page","thumbnail":h.get("company_logo_url","") or "","description":(h.get("tagline") or "")[:200],"status":status.lower()})
                params["offset"] += len(items)
                if params["offset"] >= data.get("count",0): break
                time.sleep(0.3)
            except Exception as e:
                print(f"[HackerEarth] {status}: {e}"); break
    print(f"[HackerEarth] {len(hackathons)} hackathons")
    return hackathons
