import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any
from . import models
from .config import DATABASE_URL

def _sqlite_path_from_url(url: str) -> str:
    if url.startswith("sqlite:///"):
        return url[len("sqlite:///"):]
    if url.startswith("sqlite:////"):
        return url[len("sqlite:"):]
    return url

DB_PATH = _sqlite_path_from_url(DATABASE_URL)
_conn = None

def get_conn():
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _conn.execute("PRAGMA foreign_keys = ON;")
        _conn.executescript(models.CREATE_MESSAGES_SQL)
        _conn.commit()
    return _conn

def insert_message(message_id: str, from_msisdn: str, to_msisdn: str, ts: str, text: Optional[str], created_at: Optional[str] = None) -> bool:
    conn = get_conn()
    created_at = created_at or datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    try:
        with conn:
            conn.execute(
                "INSERT INTO messages (message_id, from_msisdn, to_msisdn, ts, text, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (message_id, from_msisdn, to_msisdn, ts, text, created_at),
            )
        return True
    except sqlite3.IntegrityError:
        return False

def query_messages(limit: int, offset: int, from_msisdn: Optional[str], since: Optional[str], q: Optional[str]):
    conn = get_conn()
    params = []
    where = []

    if from_msisdn:
        where.append("from_msisdn = ?")
        params.append(from_msisdn)
    if since:
        where.append("ts >= ?")
        params.append(since)
    if q:
        where.append("LOWER(text) LIKE ?")
        params.append(f"%{q.lower()}%")

    where_sql = "WHERE " + " AND ".join(where) if where else ""

    cur = conn.execute(f"SELECT COUNT(*) as c FROM messages {where_sql}", params)
    total = cur.fetchone()["c"]

    order_sql = "ORDER BY ts ASC, message_id ASC"
    cur = conn.execute(
        f"SELECT message_id, from_msisdn as `from`, to_msisdn as `to`, ts, text FROM messages {where_sql} {order_sql} LIMIT ? OFFSET ?",
        params + [limit, offset],
    )
    data = [dict(r) for r in cur.fetchall()]

    return {"data": data, "total": total, "limit": limit, "offset": offset}

def stats_aggregate():
    conn = get_conn()

    cur = conn.execute("SELECT COUNT(*) as c FROM messages")
    total = cur.fetchone()["c"]

    cur = conn.execute(
        "SELECT from_msisdn as `from`, COUNT(*) as cnt FROM messages GROUP BY from_msisdn ORDER BY cnt DESC LIMIT 10"
    )
    rows = [{"from": r["from"], "count": r["cnt"]} for r in cur.fetchall()]

    cur = conn.execute("SELECT COUNT(DISTINCT from_msisdn) as c FROM messages")
    senders_count = cur.fetchone()["c"]

    cur = conn.execute("SELECT MIN(ts) as first_ts, MAX(ts) as last_ts FROM messages")
    r = cur.fetchone()

    return {
        "total_messages": total,
        "senders_count": senders_count,
        "messages_per_sender": rows,
        "first_message_ts": r["first_ts"],
        "last_message_ts": r["last_ts"],
    }
