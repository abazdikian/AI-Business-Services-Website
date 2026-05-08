"""Market News loader — surfaces the weekly AI-news digest and the Reddit
warm-queue scouted by the social-pipeline as a read-only tab in the hub.

Sources (both produced by existing social-pipeline cron jobs):
  - social-pipeline/digest_data/latest_digest.json — AI news items with
    curated headline/summary/caption and ready-to-post drafts
  - social-pipeline/scout_data/warm_queue.json — Reddit posts from small-
    business / entrepreneur subs ranked by opportunity_type + relevance
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from ..config import PROJECT_ROOT

log = logging.getLogger(__name__)

DIGEST_PATH = PROJECT_ROOT / "social-pipeline" / "digest_data" / "latest_digest.json"
WARMQ_PATH  = PROJECT_ROOT / "social-pipeline" / "scout_data"  / "warm_queue.json"


def _safe_load(p: Path) -> tuple[list, str | None]:
    """Load JSON; return (items, iso mtime) or ([], None) if missing."""
    if not p.exists():
        return [], None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        log.warning("bad JSON in %s: %s", p, e)
        return [], None
    mtime = datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc).isoformat(timespec="seconds")
    if not isinstance(data, list):
        return [], mtime
    return data, mtime


def load_digest() -> dict:
    items, fetched = _safe_load(DIGEST_PATH)
    return {"entries": items, "fetched_at": fetched, "source": str(DIGEST_PATH)}


def load_warm_queue() -> dict:
    items, fetched = _safe_load(WARMQ_PATH)
    # Sort by relevance_score desc then recency
    items = sorted(
        items,
        key=lambda p: (p.get("relevance_score", 0), p.get("created_utc", 0)),
        reverse=True,
    )
    return {"entries": items, "fetched_at": fetched, "source": str(WARMQ_PATH)}


def market_news_view() -> dict:
    """Single dict consumed by the template."""
    digest = load_digest()
    warm = load_warm_queue()
    return {"digest": digest, "warm_queue": warm}
