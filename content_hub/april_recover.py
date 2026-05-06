"""Recover the April digest from already-paid Apify dataset IDs (no new actor runs).

Reads dataset items via the free Apify dataset endpoint, runs them through each
channel's _to_post() mapping, applies the configured-creator + April + top-N
filters, and inserts under week_id="2026-04". Sends Alice a status email.

Usage:
    python -m content_hub.april_recover
"""

from __future__ import annotations

import logging
import os
import sys
import traceback

import httpx

from . import db
from .april_digest import (
    WEEK_ID, TOP_N_PER_CHANNEL, _allowed_handles, _engagement_score,
    _in_april, build_status_html, send_status_email,
)
from .config import APIFY_TOKEN
from .fetchers import instagram as ig_mod
from .fetchers import linkedin as li_mod
from .fetchers import tiktok as tt_mod
from .fetchers import youtube as yt_mod
from .scheduler import _enrich

logging.basicConfig(level=logging.INFO, format="%(asctime)s [recover] %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger(__name__)

# Dry-run datasets captured from successful runs at ~14:38-14:43 UTC on 2026-05-03.
DATASETS = {
    "youtube":   ["cvSs6IglacVivh0CT"],
    "linkedin":  ["TsfUHZJEcvtF8tlGS", "WPQeSwb6zkcs53FYn", "lB6exo87F2V7DMV2A", "S559nf7WTbP7poRTp"],
    "tiktok":    ["TzQfYLxkFogqfZbwM"],
    "instagram": ["sA2J7BZl06gtnvyqX"],
}

FETCHERS = {
    "youtube": yt_mod,
    "linkedin": li_mod,
    "tiktok": tt_mod,
    "instagram": ig_mod,
}


def fetch_dataset(ds_id: str) -> list[dict]:
    url = f"https://api.apify.com/v2/datasets/{ds_id}/items"
    r = httpx.get(url, params={"token": APIFY_TOKEN, "format": "json", "clean": "1"}, timeout=60)
    r.raise_for_status()
    return r.json()


def map_items_to_posts(channel: str, items: list[dict]) -> list:
    """Run raw Apify items through each channel's _to_post mapping.
    LinkedIn's _to_post takes only (item); others take (item, source).
    """
    mod = FETCHERS[channel]
    out = []
    for it in items:
        try:
            if channel == "linkedin":
                p = mod._to_post(it)
            else:
                p = mod._to_post(it, source="creator")
        except Exception as exc:
            log.debug("[%s] _to_post failed: %s", channel, exc)
            continue
        if p:
            out.append(p)
    return out


def process_channel(channel: str) -> tuple[list[dict], dict]:
    raw_items: list[dict] = []
    for ds_id in DATASETS[channel]:
        try:
            items = fetch_dataset(ds_id)
            log.info("[%s] dataset %s → %d items", channel, ds_id, len(items))
            raw_items.extend(items)
        except Exception as exc:
            log.error("[%s] failed to read %s: %s", channel, ds_id, exc)

    posts = map_items_to_posts(channel, raw_items)
    rows = [p.to_row() for p in posts]
    log.info("[%s] mapped posts: %d", channel, len(rows))

    april = [r for r in rows if _in_april(r.get("posted_at"))]
    log.info("[%s] in April 2026: %d", channel, len(april))

    allowed = _allowed_handles(channel)
    before = len(april)
    april = [r for r in april if (r.get("creator_handle") or "").lower() in allowed]
    log.info("[%s] after configured-creator filter: %d (dropped %d)", channel, len(april), before - len(april))

    for r in april:
        _enrich(r, skip_llm=True)

    april.sort(key=_engagement_score, reverse=True)
    top = april[:TOP_N_PER_CHANNEL]
    counts = {"raw": len(rows), "april": len(april), "top": len(top)}
    return top, counts


def main() -> int:
    db.init_db()

    per_channel_counts = {}
    errors = []
    all_top = []

    for channel in ["youtube", "linkedin", "tiktok", "instagram"]:
        try:
            top, counts = process_channel(channel)
        except Exception as exc:
            log.error("[%s] processing failed: %s", channel, exc)
            traceback.print_exc()
            errors.append(f"{channel}: {exc}")
            per_channel_counts[channel] = {"raw": 0, "april": 0, "top": 0}
            continue
        per_channel_counts[channel] = counts
        all_top.extend(top)
        for p in top:
            log.info("[%s] TOP @%s · likes=%d views=%d → %s",
                     channel, p.get("creator_handle") or "?",
                     p.get("likes") or 0, p.get("views") or 0,
                     p.get("post_url") or "")

    log.info("Inserting %d posts under week_id=%s", len(all_top), WEEK_ID)
    db.insert_week(WEEK_ID, all_top)

    subject = "Content Hub: April 2026 digest ready" if not errors else \
              f"Content Hub: April 2026 digest ready ({len(errors)} errors)"
    html = build_status_html(per_channel_counts, errors)
    send_status_email(subject, html)
    log.info("Done. View at http://localhost:4000/week/%s", WEEK_ID)
    return 0


if __name__ == "__main__":
    sys.exit(main())
