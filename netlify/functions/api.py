"""
HackTracker API — Netlify Serverless Function (Python)
Handles all /api/* routes.
Database: Supabase PostgreSQL via DATABASE_URL env var.
Scraping: done separately via GitHub Actions every 4 hours.
"""
import os, json, hashlib
from typing import Optional
import psycopg2, psycopg2.extras
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from mangum import Mangum

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = os.environ.get("DATABASE_URL", "")


def get_conn():
    return psycopg2.connect(DATABASE_URL, sslmode="require")


def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS hackathons (
            id TEXT PRIMARY KEY,
            source TEXT, title TEXT, url TEXT UNIQUE,
            deadline TEXT, prize TEXT, thumbnail TEXT,
            description TEXT, status TEXT DEFAULT 'open',
            first_seen TIMESTAMPTZ DEFAULT NOW(),
            notified BOOLEAN DEFAULT FALSE
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS subscribers (
            id SERIAL PRIMARY KEY,
            email TEXT UNIQUE,
            fcm_token TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    conn.commit()
    conn.close()


# Run DB init once on cold start
if DATABASE_URL:
    try:
        init_db()
    except Exception as e:
        print(f"[DB init] {e}")


class SubscribeRequest(BaseModel):
    email: Optional[str] = None
    fcm_token: Optional[str] = None


@app.get("/api")
@app.get("/api/")
def root():
    return {"status": "ok", "version": "2.0.0", "db": "connected" if DATABASE_URL else "not configured"}


@app.get("/api/hackathons")
def list_hackathons(
    limit: int = Query(100, le=500),
    source: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
):
    if not DATABASE_URL:
        return {"count": 0, "hackathons": [], "error": "DATABASE_URL not configured"}
    try:
        conn = get_conn()
        c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        clauses, params = [], []
        if source:
            clauses.append("LOWER(source) = %s")
            params.append(source.lower())
        if status:
            clauses.append("status = %s")
            params.append(status)
        if search:
            clauses.append("(LOWER(title) LIKE %s OR LOWER(description) LIKE %s)")
            q = f"%{search.lower()}%"
            params.extend([q, q])

        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.append(limit)

        c.execute(
            f"SELECT source,title,url,deadline,prize,thumbnail,description,status,first_seen "
            f"FROM hackathons {where} ORDER BY first_seen DESC LIMIT %s",
            params,
        )
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return {"count": len(rows), "hackathons": rows}
    except Exception as e:
        return {"count": 0, "hackathons": [], "error": str(e)}


@app.get("/api/hackathons/stats")
def stats():
    if not DATABASE_URL:
        return {"total": 0, "by_source": {}}
    try:
        conn = get_conn()
        c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        c.execute("SELECT source, COUNT(*) as cnt FROM hackathons GROUP BY source ORDER BY cnt DESC")
        rows = c.fetchall()
        conn.close()
        by_source = {r["source"]: r["cnt"] for r in rows}
        return {"total": sum(by_source.values()), "by_source": by_source}
    except Exception as e:
        return {"total": 0, "by_source": {}, "error": str(e)}


@app.get("/api/hackathons/sources")
def sources():
    return {
        "sources": ["Devpost", "dev.to", "lablab.ai", "MLH",
                    "HackerEarth", "DoraHacks", "Google Developers"]
    }


@app.post("/api/subscribe")
def subscribe(req: SubscribeRequest):
    if not req.email and not req.fcm_token:
        return {"error": "Provide email or fcm_token"}
    if not DATABASE_URL:
        return {"status": "error", "message": "DATABASE_URL not configured"}
    try:
        conn = get_conn()
        c = conn.cursor()
        c.execute(
            "INSERT INTO subscribers (email, fcm_token) VALUES (%s, %s) "
            "ON CONFLICT (email) DO UPDATE SET fcm_token = EXCLUDED.fcm_token",
            (req.email, req.fcm_token),
        )
        conn.commit()
        conn.close()
        return {"status": "subscribed", "email": req.email}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/api/health")
def health():
    db_ok = False
    if DATABASE_URL:
        try:
            conn = get_conn()
            conn.close()
            db_ok = True
        except Exception:
            pass
    return {"status": "healthy", "db": "connected" if db_ok else "disconnected"}


# Netlify handler
def handler(event, context):
    from mangum import Mangum
    asgi_handler = Mangum(app, lifespan="off")
    return asgi_handler(event, context)
