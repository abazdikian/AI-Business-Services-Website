"""SQLite schema + queries for the Content Hub."""

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Iterable

from .config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS weeks (
    id TEXT PRIMARY KEY,
    pulled_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS posts (
    id TEXT PRIMARY KEY,
    week_id TEXT NOT NULL,
    channel TEXT NOT NULL,
    creator_handle TEXT,
    post_url TEXT,
    thumbnail_url TEXT,
    posted_at TEXT,
    caption TEXT,
    hook_line TEXT,
    format_tag TEXT,
    likes INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    shares INTEGER DEFAULT 0,
    views INTEGER DEFAULT 0,
    engagement_rate REAL,
    why_trending TEXT,
    source TEXT,
    raw_json TEXT,
    FOREIGN KEY (week_id) REFERENCES weeks(id)
);
CREATE INDEX IF NOT EXISTS idx_posts_week_channel ON posts(week_id, channel);

CREATE TABLE IF NOT EXISTS selections (
    week_id TEXT NOT NULL,
    channel TEXT NOT NULL,
    post_id TEXT NOT NULL,
    selected_at TEXT NOT NULL,
    PRIMARY KEY (week_id, post_id)
);

CREATE TABLE IF NOT EXISTS pasted_urls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    week_id TEXT NOT NULL,
    channel TEXT NOT NULL,
    url TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    week_id TEXT NOT NULL,
    channel TEXT NOT NULL,
    status TEXT NOT NULL,
    payload_json TEXT,
    created_at TEXT NOT NULL,
    finished_at TEXT,
    result_json TEXT
);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    start_at TEXT NOT NULL,        -- ISO datetime, e.g. "2026-05-27T19:00:00-04:00"
    end_at TEXT,                    -- nullable (point-in-time events have no end)
    category TEXT NOT NULL,         -- 'webinar' | 'launch' | 'ad' | 'content' | 'community' | 'external' | 'custom'
    color TEXT,                     -- hex like '#7A1530' (overrides category default)
    source TEXT NOT NULL DEFAULT 'manual',  -- 'manual' | 'gcal' | 'recurring'
    source_id TEXT,                 -- gcal event ID or recurring rule ID; NULL for manual
    notes TEXT,
    url TEXT,                       -- optional link (zoom, ad dashboard, etc.)
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_events_start ON events(start_at);
CREATE INDEX IF NOT EXISTS idx_events_source ON events(source, source_id);
"""


@contextmanager
def conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    try:
        yield c
        c.commit()
    finally:
        c.close()


def init_db() -> None:
    with conn() as c:
        c.executescript(SCHEMA)


def insert_week(week_id: str, posts: Iterable[dict]) -> None:
    now = datetime.utcnow().isoformat()
    with conn() as c:
        c.execute(
            "INSERT OR REPLACE INTO weeks (id, pulled_at) VALUES (?, ?)",
            (week_id, now),
        )
        c.execute("DELETE FROM posts WHERE week_id = ?", (week_id,))
        for p in posts:
            c.execute(
                """INSERT OR REPLACE INTO posts
                (id, week_id, channel, creator_handle, post_url, thumbnail_url,
                 posted_at, caption, hook_line, format_tag,
                 likes, comments, shares, views, engagement_rate,
                 why_trending, source, raw_json)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    p["id"], week_id, p["channel"], p.get("creator_handle"),
                    p.get("post_url"), p.get("thumbnail_url"),
                    p.get("posted_at"), p.get("caption"), p.get("hook_line"),
                    p.get("format_tag"),
                    p.get("likes", 0), p.get("comments", 0),
                    p.get("shares", 0), p.get("views", 0),
                    p.get("engagement_rate"),
                    p.get("why_trending"), p.get("source", "creator"),
                    json.dumps(p.get("raw", {})),
                ),
            )


def list_weeks() -> list[dict]:
    with conn() as c:
        return [dict(r) for r in c.execute(
            "SELECT id, pulled_at FROM weeks ORDER BY id DESC"
        )]


# ── EVENTS ───────────────────────────────────────────────────────────────────

def events_in_range(start_iso: str, end_iso: str) -> list[dict]:
    """Events whose start_at falls in [start_iso, end_iso). ISO date or datetime ok."""
    with conn() as c:
        rows = c.execute(
            "SELECT * FROM events WHERE start_at >= ? AND start_at < ? ORDER BY start_at ASC",
            (start_iso, end_iso),
        ).fetchall()
        return [dict(r) for r in rows]


def insert_event(title: str, start_at: str, category: str,
                 end_at: str | None = None, color: str | None = None,
                 source: str = "manual", source_id: str | None = None,
                 notes: str | None = None, url: str | None = None) -> int:
    with conn() as c:
        cur = c.execute(
            """INSERT INTO events (title, start_at, end_at, category, color,
                                   source, source_id, notes, url, created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (title, start_at, end_at, category, color, source, source_id, notes, url,
             datetime.utcnow().isoformat()),
        )
        return cur.lastrowid


def upsert_event_by_source(source: str, source_id: str, **fields) -> None:
    """Used by gcal sync — replace if (source, source_id) exists, else insert."""
    with conn() as c:
        existing = c.execute(
            "SELECT id FROM events WHERE source=? AND source_id=?",
            (source, source_id),
        ).fetchone()
        cols = ["title", "start_at", "end_at", "category", "color", "notes", "url"]
        if existing:
            sets = ", ".join(f"{k}=?" for k in cols if k in fields)
            vals = [fields[k] for k in cols if k in fields]
            c.execute(f"UPDATE events SET {sets} WHERE id=?", (*vals, existing["id"]))
        else:
            insert_event(source=source, source_id=source_id, **fields)


def delete_event(event_id: int) -> None:
    with conn() as c:
        c.execute("DELETE FROM events WHERE id=? AND source='manual'", (event_id,))


def purge_events_by_source(source: str) -> int:
    """Wipe all events from a given source (used before re-syncing gcal)."""
    with conn() as c:
        cur = c.execute("DELETE FROM events WHERE source=?", (source,))
        return cur.rowcount


def purge_events_by_source_in_range(source: str, start_iso: str, end_iso: str) -> int:
    """Wipe events from a source within a date range — for month-by-month re-sync."""
    with conn() as c:
        cur = c.execute(
            "DELETE FROM events WHERE source=? AND start_at >= ? AND start_at < ?",
            (source, start_iso, end_iso),
        )
        return cur.rowcount


def current_week_id() -> str | None:
    rows = list_weeks()
    return rows[0]["id"] if rows else None


def posts_for(week_id: str, channel: str) -> list[dict]:
    with conn() as c:
        rows = c.execute(
            """SELECT p.*, CASE WHEN s.post_id IS NULL THEN 0 ELSE 1 END AS selected
               FROM posts p
               LEFT JOIN selections s ON s.post_id = p.id AND s.week_id = p.week_id
               WHERE p.week_id = ? AND p.channel = ?
               ORDER BY (COALESCE(p.engagement_rate, 0)) DESC,
                        (COALESCE(p.likes, 0) + COALESCE(p.comments, 0)) DESC""",
            (week_id, channel),
        ).fetchall()
        return [dict(r) for r in rows]


def toggle_selection(week_id: str, channel: str, post_id: str, selected: bool) -> None:
    with conn() as c:
        if selected:
            c.execute(
                "INSERT OR IGNORE INTO selections (week_id, channel, post_id, selected_at) VALUES (?,?,?,?)",
                (week_id, channel, post_id, datetime.utcnow().isoformat()),
            )
        else:
            c.execute(
                "DELETE FROM selections WHERE week_id=? AND post_id=?",
                (week_id, post_id),
            )


def get_pasted_urls(week_id: str, channel: str) -> str:
    with conn() as c:
        rows = c.execute(
            "SELECT url FROM pasted_urls WHERE week_id=? AND channel=? ORDER BY id",
            (week_id, channel),
        ).fetchall()
        return "\n".join(r["url"] for r in rows)


def set_pasted_urls(week_id: str, channel: str, text: str) -> None:
    urls = [u.strip() for u in text.splitlines() if u.strip()]
    with conn() as c:
        c.execute("DELETE FROM pasted_urls WHERE week_id=? AND channel=?", (week_id, channel))
        for u in urls:
            c.execute(
                "INSERT INTO pasted_urls (week_id, channel, url) VALUES (?,?,?)",
                (week_id, channel, u),
            )


def enqueue_job(week_id: str, channel: str, payload: dict) -> int:
    with conn() as c:
        cur = c.execute(
            "INSERT INTO jobs (week_id, channel, status, payload_json, created_at) VALUES (?,?,?,?,?)",
            (week_id, channel, "queued", json.dumps(payload), datetime.utcnow().isoformat()),
        )
        return cur.lastrowid


def latest_job_for(week_id: str, channel: str) -> dict | None:
    with conn() as c:
        row = c.execute(
            "SELECT * FROM jobs WHERE week_id=? AND channel=? ORDER BY id DESC LIMIT 1",
            (week_id, channel),
        ).fetchone()
        if not row:
            return None
        d = dict(row)
        if d.get("result_json"):
            try:
                d["result"] = json.loads(d["result_json"])
            except json.JSONDecodeError:
                d["result"] = None
        else:
            d["result"] = None
        return d


def next_queued_job() -> dict | None:
    with conn() as c:
        row = c.execute(
            "SELECT * FROM jobs WHERE status='queued' ORDER BY id ASC LIMIT 1"
        ).fetchone()
        return dict(row) if row else None


def mark_job(job_id: int, status: str, result: dict | None = None) -> None:
    with conn() as c:
        c.execute(
            "UPDATE jobs SET status=?, finished_at=?, result_json=? WHERE id=?",
            (
                status,
                datetime.utcnow().isoformat() if status in ("done", "failed") else None,
                json.dumps(result) if result else None,
                job_id,
            ),
        )


def selected_posts(week_id: str, channel: str) -> list[dict]:
    with conn() as c:
        rows = c.execute(
            """SELECT p.* FROM posts p
               JOIN selections s ON s.post_id = p.id AND s.week_id = p.week_id
               WHERE p.week_id=? AND p.channel=?""",
            (week_id, channel),
        ).fetchall()
        return [dict(r) for r in rows]


def posts_by_ids(post_ids: list[str]) -> list[dict]:
    if not post_ids:
        return []
    with conn() as c:
        placeholders = ",".join("?" for _ in post_ids)
        rows = c.execute(
            f"SELECT * FROM posts WHERE id IN ({placeholders})",
            post_ids,
        ).fetchall()
        by_id = {r["id"]: dict(r) for r in rows}
        return [by_id[i] for i in post_ids if i in by_id]
