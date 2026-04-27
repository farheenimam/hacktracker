import requests
from datetime import datetime, timedelta

HEADERS = {"User-Agent": "HackTracker/2.0"}

def scrape_mlh():
    hackathons = []
    seen = set()
    current_year = datetime.now().year

    for year in [current_year, current_year + 1]:
        try:
            r = requests.get(f"https://mlh.io/seasons/{year}/events.json", headers=HEADERS, timeout=15)
            r.raise_for_status()
            for event in r.json():
                url = event.get("url") or event.get("link", "")
                if not url or url in seen:
                    continue
                end = event.get("end_date") or event.get("endDate", "")
                if end:
                    try:
                        if datetime.strptime(end[:10], "%Y-%m-%d") < datetime.now() - timedelta(days=1):
                            continue
                    except:
                        pass
                seen.add(url)
                hackathons.append({
                    "source": "MLH",
                    "title": event.get("name") or event.get("title", ""),
                    "url": url,
                    "deadline": end[:10] if end else "TBD",
                    "prize": "MLH prizes + swag",
                    "thumbnail": event.get("image") or "",
                    "description": f"MLH hackathon in {event.get('location', 'various')}",
                    "status": "open"
                })
        except Exception as e:
            print(f"[MLH] {year}: {e}")

    # Add known Global Hack Week events
    ghw_events = [
        {
            "title": "Global Hack Week: GenAI",
            "url": "https://ghw.mlh.io",
            "deadline": "2026-05-14",
            "description": "Week-long event diving into Generative AI. Free for anyone anywhere.",
        },
        {
            "title": "Global Hack Week: Hacking for Good",
            "url": "https://ghw.mlh.io",
            "deadline": "2026-06-18",
            "description": "A week-long event dedicated to building projects to make the world a better place.",
        },
    ]

    for ghw in ghw_events:
        if ghw["url"] not in seen:
            seen.add(ghw["url"] + ghw["title"])
            hackathons.append({
                "source": "MLH",
                "title": ghw["title"],
                "url": ghw["url"],
                "deadline": ghw["deadline"],
                "prize": "MLH prizes + swag",
                "thumbnail": "",
                "description": ghw["description"],
                "status": "upcoming"
            })

    print(f"[MLH] {len(hackathons)} events")
    return hackathons