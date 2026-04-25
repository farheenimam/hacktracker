import feedparser, time
from bs4 import BeautifulSoup
KEYWORDS = ["hackathon","challenge","solution challenge","devfest","build with google","gemini","google hack","competition","code jam","kickstart"]
def scrape_google_dev_events():
    hackathons = []; seen = set()
    def add(h):
        if h.get("url") and h["url"] not in seen and h.get("title"):
            seen.add(h["url"]); hackathons.append(h)
    try:
        feed = feedparser.parse("https://developers.googleblog.com/feeds/posts/default?alt=rss")
        for entry in feed.entries[:50]:
            title = entry.get("title",""); summary = BeautifulSoup(entry.get("summary",""),"lxml").get_text()
            if not any(k in (title+" "+summary).lower() for k in KEYWORDS): continue
            add({"source":"Google Developers","title":title,"url":entry.get("link",""),"deadline":(entry.get("published","") or "")[:10],"prize":"See post","thumbnail":"","description":summary[:200],"status":"open"})
        time.sleep(0.3)
    except Exception as e:
        print(f"[Google Dev] RSS: {e}")
    add({"source":"Google Developers","title":"GDSC Solution Challenge 2026","url":"https://developers.google.com/community/gdsc-solution-challenge","deadline":"April 2026","prize":"Trip to Google HQ + mentorship","thumbnail":"","description":"Annual challenge for GDSC members. Solve UN SDG problems using Google tech.","status":"open"})
    add({"source":"Google Developers","title":"Google Code Jam 2026","url":"https://codingcompetitions.withgoogle.com/codejam","deadline":"TBD","prize":"$15,000","thumbnail":"","description":"Annual algorithmic programming competition by Google.","status":"open"})
    print(f"[Google Dev] {len(hackathons)} items")
    return hackathons
