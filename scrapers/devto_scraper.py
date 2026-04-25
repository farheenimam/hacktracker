import requests, time
BASE = "https://dev.to/api"
HEADERS = {"User-Agent":"HackTracker/2.0","Accept":"application/vnd.forem.api-v1+json"}
KEYWORDS = ["hackathon","hack ","hacks","challenge","competition","contest","build challenge",
            "game jam","game off","imagine cup","code for good","code jam","kickstart",
            "solution challenge","summer of code","gsoc","sprint","buildathon","win prizes",
            "prize pool","devpost","lablab"," mlh ","dorahacks","build with","code with","bounty program",
            "hackathon","hacktoberfest","hack week","global hack","battlecode","technica"]
TAGS = ["hackathon","hackathons","hacktoberfest","challenge","webdev","opensource","competition","gamedev","showdev"]

def _matches(a):
    combined = " ".join([a.get("title",""), a.get("description",""),
        ", ".join(a["tag_list"]) if isinstance(a.get("tag_list"),list) else str(a.get("tag_list",""))]).lower()
    return any(k in combined for k in KEYWORDS)

def _false_positive(a):
    combined = (a.get("title","")+" "+a.get("description","")).lower()
    return any(fp in combined for fp in ["how to win","tips for","tutorial","introduction to",
        "getting started","bug bounty guide","agile sprint","sprint planning"])

def scrape_devto():
    hackathons = []; seen = set()
    for tag in TAGS:
        for page in range(1, 4):
            try:
                r = requests.get(f"{BASE}/articles", headers=HEADERS,
                    params={"tag":tag,"per_page":30,"page":page,"top":365}, timeout=15)
                r.raise_for_status(); articles = r.json()
                if not articles: break
                for a in articles:
                    url = a.get("url","")
                    if not url or url in seen or not _matches(a) or _false_positive(a): continue
                    seen.add(url)
                    hackathons.append({"source":"dev.to","title":a.get("title",""),"url":url,
                        "deadline":(a.get("published_at") or "")[:10] or "TBD",
                        "prize":"See article","thumbnail":a.get("cover_image") or a.get("social_image") or "",
                        "description":a.get("description","") or "","status":"open"})
                time.sleep(0.25)
            except Exception as e:
                print(f"[dev.to] tag={tag} page={page}: {e}"); break
    print(f"[dev.to] {len(hackathons)} items")
    return hackathons
