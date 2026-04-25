import requests, time
from datetime import datetime
HEADERS = {"User-Agent":"HackTracker/2.0","Accept":"application/json","Origin":"https://dorahacks.io","Referer":"https://dorahacks.io/hackathon"}
def scrape_dorahacks():
    hackathons = []; seen = set()
    for status in ["open","upcoming"]:
        params = {"type":"hackathon","status":status,"limit":20,"offset":0}
        while True:
            try:
                r = requests.get("https://dorahacks.io/api/hackathon/list",headers=HEADERS,params=params,timeout=15)
                r.raise_for_status(); data = r.json()
                items = data.get("data",{}).get("hackathons") or data.get("hackathons") or data.get("data") or data.get("results") or []
                if not items or not isinstance(items,list): break
                for h in items:
                    url = h.get("url") or f"https://dorahacks.io/hackathon/{h.get('id','')}"
                    if not url or url in seen: continue
                    seen.add(url)
                    end = h.get("end_time") or h.get("deadline","")
                    deadline = end[:10] if end else "TBD"
                    if deadline != "TBD":
                        try:
                            if datetime.strptime(deadline,"%Y-%m-%d") < datetime.now(): continue
                        except: pass
                    hackathons.append({"source":"DoraHacks","title":h.get("title") or h.get("name",""),"url":url,"deadline":deadline,"prize":str(h.get("prize_pool") or "See page"),"thumbnail":h.get("cover") or h.get("image") or "","description":(h.get("description") or "")[:200],"status":status})
                params["offset"] += len(items)
                if len(items) < params["limit"]: break
                time.sleep(0.3)
            except Exception as e:
                print(f"[DoraHacks] {status}: {e}"); break
    print(f"[DoraHacks] {len(hackathons)} hackathons")
    return hackathons
