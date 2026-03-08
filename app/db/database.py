import sqlite3
import os
import time
import uuid
from typing import Optional

# sqlite locally, swap DATABASE_URL to postgres on aws
DB_PATH = os.getenv("DATABASE_URL", "researchnu.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    # run schema.sql once on startup
    conn = get_conn()
    with open("app/db/schema.sql", "r") as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()
    print("db initialized")

def log_query(
    query_text: str,
    user_type: str,
    novelty_score: float,
    sources_used: list,
    latency_ms: int,
    session_id: Optional[str] = None
):
    conn = get_conn()
    conn.execute(
        """INSERT INTO queries
           (session_id, query_text, user_type, novelty_score, sources_used, latency_ms)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            session_id or str(uuid.uuid4()),
            query_text,
            user_type,
            novelty_score,
            ",".join(sources_used) if sources_used else "",
            latency_ms
        )
    )
    conn.commit()
    conn.close()

def upsert_session(session_id: str, ip: str):
    conn = get_conn()
    conn.execute(
        """INSERT INTO sessions (id, ip, query_count)
           VALUES (?, ?, 1)
           ON CONFLICT(id) DO UPDATE SET
           query_count = query_count + 1,
           last_seen = CURRENT_TIMESTAMP""",
        (session_id, ip)
    )
    conn.commit()
    conn.close()

def get_session_query_count(session_id: str) -> int:
    conn = get_conn()
    row = conn.execute(
        "SELECT query_count FROM sessions WHERE id = ?", (session_id,)
    ).fetchone()
    conn.close()
    return row["query_count"] if row else 0

def recent_queries(limit: int = 10) -> list:
    conn = get_conn()
    rows = conn.execute(
        """SELECT query_text, user_type, novelty_score, sources_used, latency_ms, created_at
           FROM queries ORDER BY created_at DESC LIMIT ?""",
        (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]