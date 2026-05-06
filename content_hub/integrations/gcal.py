"""Google Calendar sync for the Marketing Calendar.

Pulls events from Alice's primary Google Calendar (abazdikian@gmail.com),
filters by keyword in event titles per `recurring_events.json → gcal_keywords`,
and upserts them into the `events` table with `source='gcal'` so they merge
naturally with manual + recurring events on /calendar/<YYYY-MM>.

Reuses OAuth from `content_hub/notify/google.py` (calendar.readonly scope).
First run will trigger a one-time browser re-consent because the scope changed.

Usage:
    python -m content_hub.integrations.gcal --sync                # current + next month
    python -m content_hub.integrations.gcal --sync --month 2026-05
    python -m content_hub.integrations.gcal --dry-run             # show matches, no DB write
"""

from __future__ import annotations

import argparse
import calendar as cal_lib
import json
import logging
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .. import db
from ..config import BASE_DIR
from ..notify.google import calendar_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s [gcal] %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger(__name__)

RECURRING_FILE = BASE_DIR / "recurring_events.json"
DEFAULT_CAL_ID = "primary"  # Alice's main calendar


def load_keywords() -> list[str]:
    if not RECURRING_FILE.exists():
        return []
    cfg = json.loads(RECURRING_FILE.read_text())
    return cfg.get("gcal_keywords", [])


def month_window(yyyy_mm: str) -> tuple[datetime, datetime]:
    y, m = (int(x) for x in yyyy_mm.split("-"))
    last = cal_lib.monthrange(y, m)[1]
    start = datetime(y, m, 1, 0, 0, 0, tzinfo=timezone.utc)
    end = datetime(y, m, last, 23, 59, 59, tzinfo=timezone.utc) + timedelta(seconds=1)
    return start, end


def matches_keywords(title: str, keywords: list[str]) -> bool:
    """Case-insensitive match with word boundaries — avoids 'AI' matching 'train'."""
    if not title:
        return False
    for kw in keywords:
        pattern = r"\b" + re.escape(kw) + r"\b"
        if re.search(pattern, title, flags=re.IGNORECASE):
            return True
    return False


def fetch_events(yyyy_mm: str, calendar_id: str = DEFAULT_CAL_ID) -> list[dict]:
    """Pull all events for the month window. No filtering yet."""
    svc = calendar_service()
    start, end = month_window(yyyy_mm)
    items: list[dict] = []
    page_token = None
    while True:
        resp = svc.events().list(
            calendarId=calendar_id,
            timeMin=start.isoformat().replace("+00:00", "Z"),
            timeMax=end.isoformat().replace("+00:00", "Z"),
            singleEvents=True,
            orderBy="startTime",
            maxResults=250,
            pageToken=page_token,
        ).execute()
        items.extend(resp.get("items", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return items


def event_to_chip(ev: dict) -> dict | None:
    title = ev.get("summary") or "(no title)"
    start = ev.get("start", {})
    end = ev.get("end", {})
    start_at = start.get("dateTime") or start.get("date")  # date for all-day
    end_at = end.get("dateTime") or end.get("date")
    if not start_at:
        return None
    return {
        "title": title.strip()[:160],
        "start_at": start_at,
        "end_at": end_at,
        "category": "external",
        "color": None,
        "url": ev.get("htmlLink"),
        "notes": (ev.get("description") or "").strip()[:280] or None,
        "source_id": ev.get("id"),
    }


def sync_month(yyyy_mm: str, calendar_id: str = DEFAULT_CAL_ID, dry_run: bool = False) -> dict:
    keywords = load_keywords()
    if not keywords:
        log.warning("No gcal_keywords in recurring_events.json — nothing will match.")
    log.info("[%s] fetching events from calendar %r…", yyyy_mm, calendar_id)
    raw = fetch_events(yyyy_mm, calendar_id)
    log.info("[%s] raw events: %d", yyyy_mm, len(raw))

    chips: list[dict] = []
    skipped: list[str] = []
    for ev in raw:
        title = ev.get("summary") or ""
        if not matches_keywords(title, keywords):
            skipped.append(title)
            continue
        chip = event_to_chip(ev)
        if chip:
            chips.append(chip)

    log.info("[%s] keyword-matched: %d (skipped %d)", yyyy_mm, len(chips), len(skipped))
    for c in chips:
        log.info("[%s]   ✓ %s · %s", yyyy_mm, c["start_at"][:16], c["title"])

    if dry_run:
        log.info("[%s] DRY RUN — no DB write.", yyyy_mm)
        return {"matched": len(chips), "skipped": len(skipped), "chips": chips}

    # Wipe prior gcal events for this month, re-upsert
    start, end = month_window(yyyy_mm)
    purged = db.purge_events_by_source_in_range("gcal", start.isoformat(), end.isoformat())
    log.info("[%s] purged %d prior gcal events", yyyy_mm, purged)
    for c in chips:
        db.insert_event(
            title=c["title"], start_at=c["start_at"], category=c["category"],
            end_at=c.get("end_at"), color=c.get("color"),
            source="gcal", source_id=c["source_id"],
            notes=c.get("notes"), url=c.get("url"),
        )
    log.info("[%s] inserted %d gcal events.", yyyy_mm, len(chips))
    return {"matched": len(chips), "skipped": len(skipped), "chips": chips}


def sync_window(months: list[str], calendar_id: str = DEFAULT_CAL_ID, dry_run: bool = False) -> dict:
    db.init_db()
    out = {}
    for m in months:
        out[m] = sync_month(m, calendar_id=calendar_id, dry_run=dry_run)
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sync", action="store_true", help="Sync gcal events into the DB")
    parser.add_argument("--dry-run", action="store_true", help="Fetch + filter only; no DB write")
    parser.add_argument("--month", help="YYYY-MM (default: current + next)")
    parser.add_argument("--calendar-id", default=DEFAULT_CAL_ID, help="Google Calendar ID (default: 'primary')")
    args = parser.parse_args()

    if not (args.sync or args.dry_run):
        parser.error("Pass --sync or --dry-run")

    if args.month:
        months = [args.month]
    else:
        today = datetime.now()
        cur = today.strftime("%Y-%m")
        nxt_y, nxt_m = (today.year + 1, 1) if today.month == 12 else (today.year, today.month + 1)
        months = [cur, f"{nxt_y:04d}-{nxt_m:02d}"]

    sync_window(months, calendar_id=args.calendar_id, dry_run=args.dry_run)
    log.info("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
