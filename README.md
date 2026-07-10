# HackTracker

Hackathon aggregator PWA. Scrapes multiple platforms, stores results in Postgres, notifies users of new hackathons.

**Live:** https://sparkling-caramel-f4396e.netlify.app
**Repo:** https://github.com/farheenimam/hacktracker

## Stack

- **Backend:** Python (native handler, no FastAPI/Mangum) — Netlify Functions
- **DB:** Supabase Postgres (Transaction Pooler)
- **Frontend:** Vanilla HTML/CSS/JS PWA, service worker, offline support
- **Automation:** GitHub Actions cron (every 4h) runs scrapers, writes to DB
- **Notifications:** Gmail SMTP (email), Firebase (push)

## Sources scraped

Devpost, dev.to, lablab.ai, MLH, HackerEarth, DoraHacks, Google Developers — matched against 100+ keywords beyond "hackathon" (game jams, GSoC, build challenges, etc).

## Architecture

```
GitHub Actions (cron, 4h) → scrapers → Supabase Postgres
Netlify Function (api.py) → reads Supabase → JSON API
Frontend (PWA) → fetches API → renders + caches offline
```

Dedup via URL hashing.

## Setup

**Env vars** (GitHub Secrets + Netlify env):
```
DATABASE_URL=postgresql://postgres.gawyuzgbaubpszajsfdj:[PASSWORD]@aws-1-ap-south-1.pooler.supabase.com:5432/postgres
```

**Local:**
```bash
pip install -r requirements.txt
python scrapers/run_all.py
```

**Deploy:** push to main → Netlify auto-deploys frontend + functions.

## Project structure

```
netlify/functions/api.py   # serverless API, native handler
scrapers/                  # one module per platform
frontend/                  # PWA (html/css/js, sw.js, manifest.json)
.github/workflows/         # cron scraper job
```

## Known issues

- MLH scraper occasionally surfaces ended events — needs filtering fix
- Stale/ended hackathons require periodic manual cleanup via Supabase SQL Editor

## Requirements

```
psycopg2-binary==2.9.9
```
