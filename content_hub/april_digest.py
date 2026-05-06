"""One-off: pull April 2026 viral posts per channel into the Content Hub.

Adds a new dropdown entry "2026-04" with the top 5 posts per channel, ranked
by engagement. No Claude tokens spent (skip_llm=True). Sends a status email
to Alice when done.

Usage:
    python -m content_hub.april_digest               # full run
    python -m content_hub.april_digest --dry-run     # fetch + filter + rank, no DB write, no email
"""

from __future__ import annotations

import argparse
import logging
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

from . import db
from .config import CHANNELS, CREATORS, BASE_DIR
from .fetchers import instagram as ig_mod
from .fetchers import linkedin as li_mod
from .fetchers import tiktok as tt_mod
from .fetchers import youtube as yt_mod
from .scheduler import _enrich

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [april_digest] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

WEEK_ID = "2026-04"
APRIL_START = datetime(2026, 4, 1, tzinfo=timezone.utc)
APRIL_END = datetime(2026, 5, 1, tzinfo=timezone.utc)
PER_CREATOR = 15
TOP_N_PER_CHANNEL = 5
LOOKBACK_DAYS_OVERRIDE = 40

FETCHERS = {
    "youtube": yt_mod,
    "linkedin": li_mod,
    "tiktok": tt_mod,
    "instagram": ig_mod,
}


def _patch_lookback() -> None:
    """Lift the 7-day filter on each fetcher so April posts pass through."""
    for mod in FETCHERS.values():
        mod.LOOKBACK_DAYS = LOOKBACK_DAYS_OVERRIDE


def _handle_from_url(url: str) -> str:
    """Extract the handle from a creator URL (works for YT/TT @handle, IG /handle/, LI /in/handle/)."""
    last = url.rstrip("/").split("?")[0].split("/")[-1]
    return last.lstrip("@").lower()


def _allowed_handles(channel: str) -> set[str]:
    return {_handle_from_url(u) for u in CREATORS.get(channel, [])}


def _in_april(posted_at_iso: str | None) -> bool:
    if not posted_at_iso:
        return False
    try:
        dt = datetime.fromisoformat(posted_at_iso.replace("Z", "+00:00"))
    except ValueError:
        return False
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return APRIL_START <= dt < APRIL_END


def _engagement_score(p: dict) -> tuple:
    """Sort key — engagement_rate first (when available), then raw interactions."""
    er = p.get("engagement_rate") or 0.0
    raw = (p.get("likes") or 0) + (p.get("comments") or 0) + (p.get("shares") or 0) + (p.get("views") or 0) // 10
    return (er, raw)


def fetch_channel(channel: str) -> tuple[list[dict], list[dict]]:
    """Returns (top_n_april_posts, all_april_posts) for one channel."""
    mod = FETCHERS[channel]
    urls = CREATORS.get(channel, [])
    log.info("[%s] fetching %d creators × %d posts…", channel, len(urls), PER_CREATOR)
    posts = mod.fetch_creators(urls, PER_CREATOR)
    log.info("[%s]   raw posts returned: %d", channel, len(posts))

    rows = [p.to_row() for p in posts]
    april = [r for r in rows if _in_april(r.get("posted_at"))]
    log.info("[%s]   in April 2026: %d", channel, len(april))

    allowed = _allowed_handles(channel)
    before = len(april)
    april = [r for r in april if (r.get("creator_handle") or "").lower() in allowed]
    if before != len(april):
        log.info("[%s]   after configured-creator filter: %d (dropped %d off-list)", channel, len(april), before - len(april))

    for r in april:
        _enrich(r, skip_llm=True)

    april.sort(key=_engagement_score, reverse=True)
    top = april[:TOP_N_PER_CHANNEL]
    return top, april


def build_status_html(per_channel_counts: dict[str, dict], errors: list[str]) -> str:
    rows = "".join(
        f"<tr><td style='padding:6px 14px;'>{ch}</td>"
        f"<td style='padding:6px 14px;text-align:right;'>{c['raw']}</td>"
        f"<td style='padding:6px 14px;text-align:right;'>{c['april']}</td>"
        f"<td style='padding:6px 14px;text-align:right;font-weight:700;color:#7A1530;'>{c['top']}</td></tr>"
        for ch, c in per_channel_counts.items()
    )
    err_block = ""
    if errors:
        err_items = "".join(f"<li style='margin-bottom:6px;'>{e}</li>" for e in errors)
        err_block = (
            f"<h3 style='color:#C13558;font-family:Georgia,serif;margin-top:24px;'>Errors</h3>"
            f"<ul style='color:#6B5A5F;'>{err_items}</ul>"
        )
    return f"""
    <html><body style="font-family:'Helvetica Neue',Arial,sans-serif;background:#F7F3EE;padding:32px;color:#2B1A1F;">
      <div style="max-width:560px;margin:0 auto;background:#fff;border-radius:18px;padding:36px;border:1px solid #EFE8E3;">
        <p style="font-size:11px;letter-spacing:.22em;text-transform:uppercase;color:#A87B1F;margin:0 0 8px;font-weight:800;">Content Hub · Process Update</p>
        <h1 style="font-family:Georgia,serif;font-weight:500;font-size:26px;line-height:1.2;margin:0 0 6px;color:#7A1530;">April 2026 viral digest is ready.</h1>
        <p style="margin:0 0 22px;color:#6B5A5F;">Top {TOP_N_PER_CHANNEL} posts per channel are now live in the hub under the <strong>2026-04</strong> dropdown entry.</p>
        <p style="margin:0 0 22px;"><a href="http://localhost:4000/week/{WEEK_ID}" style="display:inline-block;background:#7A1530;color:#fff;padding:12px 22px;border-radius:999px;text-decoration:none;font-weight:700;">Open localhost:4000/week/{WEEK_ID} →</a></p>
        <table style="width:100%;border-collapse:collapse;font-size:14px;color:#2B1A1F;">
          <thead>
            <tr style="border-bottom:1px solid #EFE8E3;">
              <th style="padding:8px 14px;text-align:left;font-weight:700;">Channel</th>
              <th style="padding:8px 14px;text-align:right;font-weight:700;">Raw fetched</th>
              <th style="padding:8px 14px;text-align:right;font-weight:700;">In April</th>
              <th style="padding:8px 14px;text-align:right;font-weight:700;">Inserted</th>
            </tr>
          </thead>
          <tbody>{rows}</tbody>
        </table>
        {err_block}
        <p style="margin:28px 0 0;font-size:12px;color:#9B8E92;">No Claude tokens spent on this run · {LOOKBACK_DAYS_OVERRIDE}-day lookback override · {PER_CREATOR} posts per creator.</p>
      </div>
    </body></html>
    """


def send_status_email(subject: str, html: str) -> None:
    """Reuse social-pipeline's Gmail OAuth send. Adds social-pipeline to sys.path."""
    sp_path = (BASE_DIR.parent / "social-pipeline").resolve()
    if str(sp_path) not in sys.path:
        sys.path.insert(0, str(sp_path))
    try:
        from send_email import send_email  # type: ignore
        send_email(subject, html)
    except Exception as exc:
        log.warning("Email send failed: %s", exc)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Skip DB write and email")
    args = parser.parse_args()

    _patch_lookback()
    db.init_db()

    per_channel_counts: dict[str, dict] = {}
    errors: list[str] = []
    all_top_posts: list[dict] = []

    for channel in CHANNELS:
        try:
            top, april_all = fetch_channel(channel)
        except Exception as exc:
            log.error("[%s] fetch failed: %s", channel, exc)
            errors.append(f"{channel}: {exc}")
            per_channel_counts[channel] = {"raw": 0, "april": 0, "top": 0}
            continue

        per_channel_counts[channel] = {
            "raw": len(april_all),
            "april": len(april_all),
            "top": len(top),
        }
        all_top_posts.extend(top)
        for p in top:
            log.info(
                "[%s] TOP @%s · likes=%d views=%d → %s",
                channel,
                p.get("creator_handle") or "?",
                p.get("likes") or 0,
                p.get("views") or 0,
                p.get("post_url") or "",
            )

    log.info(
        "Summary: %s",
        ", ".join(f"{ch}={c['top']}/{c['april']}" for ch, c in per_channel_counts.items()),
    )

    if args.dry_run:
        log.info("Dry run — skipping DB insert and email.")
        return 0

    log.info("Inserting %d posts under week_id=%s", len(all_top_posts), WEEK_ID)
    db.insert_week(WEEK_ID, all_top_posts)

    subject = "Content Hub: April 2026 digest ready" if not errors else \
              f"Content Hub: April 2026 digest ready (with {len(errors)} errors)"
    html = build_status_html(per_channel_counts, errors)
    send_status_email(subject, html)
    log.info("Done. View at http://localhost:4000/week/%s", WEEK_ID)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        traceback.print_exc()
        sys.exit(1)
