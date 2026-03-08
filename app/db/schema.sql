-- researchnu query log and session tracking
-- works with sqlite locally, postgres on aws (same queries)

CREATE TABLE IF NOT EXISTS queries (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  TEXT,
    query_text  TEXT NOT NULL,
    user_type   TEXT NOT NULL,
    novelty_score REAL,
    sources_used  TEXT,
    latency_ms    INTEGER,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sessions (
    id          TEXT PRIMARY KEY,
    ip          TEXT,
    query_count INTEGER DEFAULT 0,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_queries_created ON queries(created_at);
CREATE INDEX IF NOT EXISTS idx_queries_user_type ON queries(user_type);
CREATE INDEX IF NOT EXISTS idx_sessions_ip ON sessions(ip);