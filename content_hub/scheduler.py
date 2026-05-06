"""Weekly pull: Apify → enrich → SQLite.

Run manually:
  python -m content_hub.scheduler           # live pull
  python -m content_hub.scheduler --fixtures # seed fixture data (no API calls)
  python -m content_hub.scheduler --dry-run  # fetch but don't write to DB
"""

import argparse
import json
import logging
from datetime import date, datetime, timedelta
from pathlib import Path

from . import db
from .config import (CHANNELS, CREATORS, CREATOR_POSTS_OVERRIDE,
                     CREATOR_POSTS_PER_CHANNEL, FIXTURES_DIR,
                     HASHTAG_POSTS_PER_CHANNEL, HASHTAGS)
from .enrich import engagement_rate, extract_hook, format_tag_for, why_trending
from .fetchers import FETCHERS

log = logging.getLogger(__name__)


def week_id_for(d: date | None = None) -> str:
    d = d or date.today()
    monday = d - timedelta(days=d.weekday())
    return monday.isoformat()


def _enrich(post: dict, skip_llm: bool) -> dict:
    post["hook_line"] = extract_hook(post.get("caption", ""))
    post["format_tag"] = format_tag_for(post["channel"], post.get("media_type"))
    post["engagement_rate"] = engagement_rate(
        post.get("likes", 0), post.get("comments", 0),
        post.get("shares", 0), post.get("followers"),
    )
    post["why_trending"] = "" if skip_llm else why_trending(
        post.get("caption", ""), post["channel"], post["format_tag"],
    )
    return post


def pull_week(week_id: str, skip_llm: bool = False) -> list[dict]:
    all_posts: list[dict] = []
    for channel in CHANNELS:
        mod = FETCHERS[channel]
        log.info("Pulling %s creators…", channel)
        per_creator = CREATOR_POSTS_OVERRIDE.get(channel, CREATOR_POSTS_PER_CHANNEL)
        creator_posts = mod.fetch_creators(CREATORS.get(channel, []), per_creator)
        log.info("  got %d creator posts", len(creator_posts))
        log.info("Pulling %s hashtags…", channel)
        hashtag_posts = mod.fetch_hashtags(HASHTAGS.get(channel, []), HASHTAG_POSTS_PER_CHANNEL)
        log.info("  got %d hashtag posts", len(hashtag_posts))
        for p in creator_posts + hashtag_posts:
            row = p.to_row()
            all_posts.append(_enrich(row, skip_llm))
    return all_posts


def seed_fixtures() -> list[dict]:
    path = FIXTURES_DIR / "sample_week.json"
    if not path.exists():
        raise FileNotFoundError(f"Missing fixture: {path}")
    posts = json.loads(path.read_text())
    for p in posts:
        _enrich(p, skip_llm=True)
    return posts


def reparse_week(week_id: str, skip_llm: bool = True) -> int:
    """Re-run fetcher mappings + enrichers on existing raw_json — no Apify calls."""
    import json
    import sqlite3
    from .config import DB_PATH
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    rows = c.execute(
        "SELECT id, channel, raw_json FROM posts WHERE week_id=?", (week_id,)
    ).fetchall()
    updated = 0
    for row in rows:
        raw = json.loads(row["raw_json"] or "{}")
        if not raw:
            continue
        mod = FETCHERS[row["channel"]]
        try:
            new_post = mod._to_post(raw) if row["channel"] in ("linkedin", "facebook") else mod._to_post(raw, source="creator")
        except Exception:
            continue
        if not new_post:
            continue
        d = new_post.to_row()
        _enrich(d, skip_llm=skip_llm)
        c.execute(
            """UPDATE posts SET creator_handle=?, post_url=?, thumbnail_url=?,
               posted_at=?, caption=?, hook_line=?, format_tag=?,
               likes=?, comments=?, shares=?, views=?, engagement_rate=?
               WHERE id=?""",
            (
                d.get("creator_handle"), d.get("post_url"), d.get("thumbnail_url"),
                d.get("posted_at"), d.get("caption"), d.get("hook_line"),
                d.get("format_tag"),
                d.get("likes", 0), d.get("comments", 0),
                d.get("shares", 0), d.get("views", 0),
                d.get("engagement_rate"),
                row["id"],
            ),
        )
        updated += 1
    c.commit()
    c.close()
    return updated


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixtures", action="store_true", help="Seed from fixtures (no API calls)")
    parser.add_argument("--dry-run", action="store_true", help="Fetch but don't write")
    parser.add_argument("--skip-llm", action="store_true", help="Skip why_trending Haiku calls")
    parser.add_argument("--reparse", action="store_true", help="Re-parse raw_json for current week (no Apify)")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    db.init_db()

    wid = week_id_for()
    if args.reparse:
        n = reparse_week(wid, skip_llm=True)
        log.info("Reparsed %d posts for week %s (kept existing why_trending).", n, wid)
        return
    if args.fixtures:
        posts = seed_fixtures()
        for p in posts:
            p["week_id"] = wid
    else:
        posts = pull_week(wid, skip_llm=args.skip_llm)

    log.info("Total posts: %d", len(posts))
    if args.dry_run:
        log.info("Dry run — not writing.")
        return
    db.insert_week(wid, posts)
    log.info("Wrote week %s with %d posts.", wid, len(posts))


if __name__ == "__main__":
    main()
