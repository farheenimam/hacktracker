import os
import json
import ssl
from urllib.parse import urlparse
import pg8000.dbapi

DATABASE_URL = os.environ.get("DATABASE_URL", "")

_HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
}


def respond(data, code=200):
    return {"statusCode": code, "headers": _HEADERS, "body": json.dumps(data, default=str)}


def get_conn():
    url = urlparse(DATABASE_URL)
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    return pg8000.dbapi.connect(
        host=url.hostname,
        port=url.port or 5432,
        database=url.path.lstrip("/"),
        user=url.username,
        password=url.password,
        ssl_context=ssl_ctx,
    )


def fetchdicts(cursor):
    cols = [d[0] for d in cursor.description]
    return [dict(zip(cols, row)) for row in cursor.fetchall()]


def handle_health():
    db_ok = False
    if DATABASE_URL:
        try:
            conn = get_conn()
            conn.close()
            db_ok = True
        except Exception:
            pass
    return respond({"status": "healthy", "db": "connected" if db_ok else "disconnected"})


def handle_hackathons(params):
    if not DATABASE_URL:
        return respond({"count": 0, "hackathons": [], "error": "DATABASE_URL not configured"})
    try:
        limit = min(int(params.get("limit", 100)), 500)
        source = params.get("source")
        status = params.get("status")
        search = params.get("search")

        conn = get_conn()
        c = conn.cursor()

        clauses, args = [], []
        if source:
            clauses.append("LOWER(source) = %s")
            args.append(source.lower())
        if status:
            clauses.append("status = %s")
            args.append(status)
        if search:
            clauses.append("(LOWER(title) LIKE %s OR LOWER(description) LIKE %s)")
            q = f"%{search.lower()}%"
            args.extend([q, q])

        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        args.append(limit)

        c.execute(
            f"SELECT source,title,url,deadline,prize,thumbnail,description,status,first_seen "
            f"FROM hackathons {where} ORDER BY first_seen DESC LIMIT %s",
            args,
        )
        rows = fetchdicts(c)
        conn.close()
        return respond({"count": len(rows), "hackathons": rows})
    except Exception as e:
        return respond({"count": 0, "hackathons": [], "error": str(e)})


def handle_stats():
    if not DATABASE_URL:
        return respond({"total": 0, "by_source": {}})
    try:
        conn = get_conn()
        c = conn.cursor()
        c.execute("SELECT source, COUNT(*) as cnt FROM hackathons GROUP BY source ORDER BY cnt DESC")
        rows = fetchdicts(c)
        conn.close()
        by_source = {r["source"]: int(r["cnt"]) for r in rows}
        return respond({"total": sum(by_source.values()), "by_source": by_source})
    except Exception as e:
        return respond({"total": 0, "by_source": {}, "error": str(e)})


def handle_sources():
    return respond({
        "sources": ["Devpost", "dev.to", "lablab.ai", "MLH",
                    "HackerEarth", "DoraHacks", "Google Developers"]
    })


def handle_subscribe(body):
    email = body.get("email")
    fcm_token = body.get("fcm_token")
    if not email and not fcm_token:
        return respond({"error": "Provide email or fcm_token"}, 400)
    if not DATABASE_URL:
        return respond({"status": "error", "message": "DATABASE_URL not configured"})
    try:
        conn = get_conn()
        c = conn.cursor()
        c.execute(
            "INSERT INTO subscribers (email, fcm_token) VALUES (%s, %s) "
            "ON CONFLICT (email) DO UPDATE SET fcm_token = EXCLUDED.fcm_token",
            (email, fcm_token),
        )
        conn.commit()
        conn.close()
        return respond({"status": "subscribed", "email": email})
    except Exception as e:
        return respond({"status": "error", "message": str(e)})


def handler(event, context):
    method = event.get("httpMethod", "GET").upper()
    path = event.get("path", "/")
    params = event.get("queryStringParameters") or {}

    if method == "OPTIONS":
        return {"statusCode": 200, "headers": _HEADERS, "body": ""}

    # Normalize: strip /api prefix so routes work regardless of redirect style.
    # Netlify may pass either "/api/health" (original path) or "/health" (splat).
    if path.startswith("/api"):
        path = path[4:] or "/"

    if path in ("/", ""):
        return respond({"status": "ok", "version": "2.0.0",
                        "db": "connected" if DATABASE_URL else "not configured"})

    if method == "GET":
        if path == "/health":
            return handle_health()
        if path == "/hackathons":
            return handle_hackathons(params)
        if path == "/hackathons/stats":
            return handle_stats()
        if path == "/hackathons/sources":
            return handle_sources()

    if method == "POST" and path == "/subscribe":
        try:
            body = json.loads(event.get("body") or "{}")
        except Exception:
            body = {}
        return handle_subscribe(body)

    return respond({"error": "Not found"}, 404)
