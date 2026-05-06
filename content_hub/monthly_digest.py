"""Monthly viral-creator digest into the Content Hub.

Generalises april_digest.py to any month. Adds:
  • Apify quota pre-flight (aborts if remaining credit too low)
  • Dataset-id capture per channel (so a re-run can recover for FREE)
  • --from-cache mode that re-reads cached dataset items, zero Apify spend

Usage:
    python -m content_hub.monthly_digest --month 2026-04                # full run
    python -m content_hub.monthly_digest --month 2026-04 --dry-run      # fetch, no DB/email
    python -m content_hub.monthly_digest --month 2026-04 --from-cache   # zero Apify, replays saved datasets
"""

from __future__ import annotations

import argparse
import calendar
import json
import logging
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

import httpx

from . import db
from .config import APIFY_TOKEN, BASE_DIR, CHANNELS, CREATORS
from .fetchers import instagram as ig_mod
from .fetchers import linkedin as li_mod
from .fetchers import tiktok as tt_mod
from .fetchers import youtube as yt_mod
from .scheduler import _enrich

logging.basicConfig(level=logging.INFO, format="%(asctime)s [monthly_digest] %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger(__name__)

PER_CREATOR = 15
TOP_N_PER_CHANNEL = 0  # 0 = no cap, insert ALL configured-creator posts in the month
LOOKBACK_DAYS_OVERRIDE = 60
MIN_QUOTA_HEADROOM_USD = 1.0
HISTORY_DIR = BASE_DIR / "digest_history"

FETCHERS = {
    "youtube": yt_mod,
    "linkedin": li_mod,
    "tiktok": tt_mod,
    "instagram": ig_mod,
}


def parse_month(s: str) -> tuple[str, datetime, datetime]:
    """'2026-04' → (week_id, start_utc, end_utc_exclusive)."""
    y, m = map(int, s.split("-"))
    last_day = calendar.monthrange(y, m)[1]
    start = datetime(y, m, 1, tzinfo=timezone.utc)
    end = datetime(y, m, last_day, 23, 59, 59, tzinfo=timezone.utc)
    end_exclusive = datetime(y + (m // 12), (m % 12) + 1, 1, tzinfo=timezone.utc)
    return s, start, end_exclusive


def patch_lookback() -> None:
    for mod in FETCHERS.values():
        mod.LOOKBACK_DAYS = LOOKBACK_DAYS_OVERRIDE


def handle_from_url(url: str) -> str:
    last = url.rstrip("/").split("?")[0].split("/")[-1]
    return last.lstrip("@").lower()


def allowed_handles(channel: str) -> set[str]:
    return {handle_from_url(u) for u in CREATORS.get(channel, [])}


def in_window(posted_at_iso: str | None, start: datetime, end: datetime) -> bool:
    if not posted_at_iso:
        return False
    try:
        d = datetime.fromisoformat(posted_at_iso.replace("Z", "+00:00"))
    except ValueError:
        return False
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return start <= d < end


def engagement_score(p: dict) -> tuple:
    er = p.get("engagement_rate") or 0.0
    raw = (p.get("likes") or 0) + (p.get("comments") or 0) + (p.get("shares") or 0) + (p.get("views") or 0) // 10
    return (er, raw)


def apify_quota_remaining() -> tuple[float, float]:
    """Returns (used_usd, max_usd). Raises on auth failure."""
    r = httpx.get(
        "https://api.apify.com/v2/users/me/limits",
        params={"token": APIFY_TOKEN}, timeout=10,
    )
    r.raise_for_status()
    d = r.json()["data"]
    return d["current"]["monthlyUsageUsd"], d["limits"]["maxMonthlyUsageUsd"]


def fetch_dataset(ds_id: str) -> list[dict]:
    r = httpx.get(
        f"https://api.apify.com/v2/datasets/{ds_id}/items",
        params={"token": APIFY_TOKEN, "format": "json", "clean": "1"},
        timeout=60,
    )
    r.raise_for_status()
    return r.json()


def map_items(channel: str, items: list[dict]) -> list:
    mod = FETCHERS[channel]
    out = []
    for it in items:
        try:
            p = mod._to_post(it) if channel == "linkedin" else mod._to_post(it, source="creator")
        except Exception:
            continue
        if p:
            out.append(p)
    return out


def fetch_channel_from_apify(channel: str) -> tuple[list, list[str]]:
    """Live Apify run. Returns (Post objects, list of dataset IDs created)."""
    mod = FETCHERS[channel]
    urls = CREATORS.get(channel, [])
    log.info("[%s] fetching %d creators × %d posts (live Apify)…", channel, len(urls), PER_CREATOR)
    posts_before = len_dataset_runs()
    posts = mod.fetch_creators(urls, PER_CREATOR)
    new_dataset_ids = recent_dataset_ids_for_actor(mod_to_actor_id(channel), since_count=posts_before)
    log.info("[%s] raw posts: %d  new datasets captured: %s", channel, len(posts), new_dataset_ids)
    return posts, new_dataset_ids


def fetch_channel_from_cache(channel: str, dataset_ids: list[str]) -> list:
    items: list[dict] = []
    for ds in dataset_ids:
        try:
            chunk = fetch_dataset(ds)
            log.info("[%s] dataset %s → %d items", channel, ds, len(chunk))
            items.extend(chunk)
        except Exception as exc:
            log.error("[%s] cache read failed for %s: %s", channel, ds, exc)
    return map_items(channel, items)


def len_dataset_runs() -> int:
    """Total successful run count today — used as a marker to detect newly-created runs."""
    try:
        r = httpx.get(
            "https://api.apify.com/v2/actor-runs",
            params={"token": APIFY_TOKEN, "desc": "true", "limit": 100, "status": "SUCCEEDED"},
            timeout=10,
        )
        r.raise_for_status()
        return len(r.json()["data"]["items"])
    except Exception:
        return 0


def recent_dataset_ids_for_actor(actor_id: str | None, since_count: int = 0) -> list[str]:
    if not actor_id:
        return []
    try:
        r = httpx.get(
            "https://api.apify.com/v2/actor-runs",
            params={"token": APIFY_TOKEN, "desc": "true", "limit": 30, "status": "SUCCEEDED"},
            timeout=10,
        )
        r.raise_for_status()
        items = r.json()["data"]["items"]
        return [it["defaultDatasetId"] for it in items if it.get("actId") == actor_id][:8]
    except Exception:
        return []


def mod_to_actor_id(channel: str) -> str | None:
    """Get actor IDs from API by name."""
    name = {
        "youtube": "streamers/youtube-scraper",
        "linkedin": "apimaestro/linkedin-profile-posts",
        "tiktok": "clockworks/tiktok-scraper",
        "instagram": "apify/instagram-scraper",
    }[channel]
    try:
        r = httpx.get(
            f"https://api.apify.com/v2/acts/{name.replace('/', '~')}",
            params={"token": APIFY_TOKEN}, timeout=10,
        )
        r.raise_for_status()
        return r.json()["data"]["id"]
    except Exception:
        return None


def history_path(month: str) -> Path:
    HISTORY_DIR.mkdir(exist_ok=True)
    return HISTORY_DIR / f"{month}.json"


def save_history(month: str, dataset_ids: dict[str, list[str]]) -> None:
    history_path(month).write_text(json.dumps({
        "month": month,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "datasets": dataset_ids,
    }, indent=2))


def load_history(month: str) -> dict[str, list[str]]:
    p = history_path(month)
    if not p.exists():
        return {}
    return json.loads(p.read_text()).get("datasets", {})


def process_channel(channel: str, posts: list, start: datetime, end: datetime) -> tuple[list[dict], dict]:
    rows = [p.to_row() for p in posts]
    in_month = [r for r in rows if in_window(r.get("posted_at"), start, end)]
    allowed = allowed_handles(channel)
    before = len(in_month)
    in_month = [r for r in in_month if (r.get("creator_handle") or "").lower() in allowed]
    log.info("[%s] mapped=%d in_month=%d configured=%d", channel, len(rows), before, len(in_month))
    for r in in_month:
        _enrich(r, skip_llm=True)
    in_month.sort(key=engagement_score, reverse=True)
    top = in_month[:TOP_N_PER_CHANNEL]
    return top, {"raw": len(rows), "month": len(in_month), "top": len(top)}


def build_status_html(month: str, counts: dict, errors: list[str], used: float, cap: float) -> str:
    rows = "".join(
        f"<tr><td style='padding:6px 14px;'>{ch}</td>"
        f"<td style='padding:6px 14px;text-align:right;'>{c['raw']}</td>"
        f"<td style='padding:6px 14px;text-align:right;'>{c['month']}</td>"
        f"<td style='padding:6px 14px;text-align:right;font-weight:700;color:#7A1530;'>{c['top']}</td></tr>"
        for ch, c in counts.items()
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
        <p style="font-size:11px;letter-spacing:.22em;text-transform:uppercase;color:#A87B1F;margin:0 0 8px;font-weight:800;">Content Hub · Monthly digest</p>
        <h1 style="font-family:Georgia,serif;font-weight:500;font-size:26px;line-height:1.2;margin:0 0 6px;color:#7A1530;">{month} viral digest is ready.</h1>
        <p style="margin:0 0 22px;color:#6B5A5F;">Top {TOP_N_PER_CHANNEL} posts per channel are now live in the hub under the <strong>{month}</strong> dropdown entry.</p>
        <p style="margin:0 0 22px;"><a href="http://localhost:4000/week/{month}" style="display:inline-block;background:#7A1530;color:#fff;padding:12px 22px;border-radius:999px;text-decoration:none;font-weight:700;">Open localhost:4000/week/{month} →</a></p>
        <table style="width:100%;border-collapse:collapse;font-size:14px;color:#2B1A1F;">
          <thead><tr style="border-bottom:1px solid #EFE8E3;"><th style="padding:8px 14px;text-align:left;font-weight:700;">Channel</th><th style="padding:8px 14px;text-align:right;font-weight:700;">Raw</th><th style="padding:8px 14px;text-align:right;font-weight:700;">In month</th><th style="padding:8px 14px;text-align:right;font-weight:700;">Inserted</th></tr></thead>
          <tbody>{rows}</tbody>
        </table>
        {err_block}
        <p style="margin:28px 0 0;font-size:12px;color:#9B8E92;">No Claude tokens spent · Apify usage: ${used:.2f} / ${cap:.0f} cap.</p>
      </div>
    </body></html>
    """


def send_status_email(subject: str, html: str) -> None:
    sp_path = (BASE_DIR.parent / "social-pipeline").resolve()
    if str(sp_path) not in sys.path:
        sys.path.insert(0, str(sp_path))
    try:
        from send_email import send_email  # type: ignore
        send_email(subject, html)
    except Exception as exc:
        log.warning("Email send failed: %s", exc)


def main() -> int:
    global TOP_N_PER_CHANNEL
    parser = argparse.ArgumentParser()
    parser.add_argument("--month", required=True, help="YYYY-MM, e.g. 2026-04")
    parser.add_argument("--dry-run", action="store_true", help="No DB write or email")
    parser.add_argument("--from-cache", action="store_true", help="Re-read saved Apify datasets — zero Apify spend")
    parser.add_argument("--force", action="store_true", help="Skip the quota pre-flight gate")
    parser.add_argument("--top-n", type=int, default=TOP_N_PER_CHANNEL,
                        help=f"Posts per channel to insert (default: {TOP_N_PER_CHANNEL}, use 0 for ALL configured-creator posts in the month)")
    args = parser.parse_args()
    TOP_N_PER_CHANNEL = args.top_n if args.top_n > 0 else 10**6

    month, start, end = parse_month(args.month)
    patch_lookback()
    db.init_db()

    used, cap = 0.0, 5.0
    if not args.from_cache:
        try:
            used, cap = apify_quota_remaining()
            remaining = cap - used
            log.info("Apify quota: used $%.2f / $%.2f cap (remaining $%.2f)", used, cap, remaining)
            if not args.force and remaining < MIN_QUOTA_HEADROOM_USD:
                log.error("ABORT: Apify remaining $%.2f below $%.2f headroom. "
                          "Re-run with --from-cache (if a recent dry-run exists) or --force to override.",
                          remaining, MIN_QUOTA_HEADROOM_USD)
                return 2
        except Exception as exc:
            log.warning("Could not check Apify quota: %s", exc)

    cached = load_history(month) if args.from_cache else {}
    if args.from_cache and not cached:
        log.error("ABORT: --from-cache requested but no history file at %s", history_path(month))
        return 2

    counts: dict = {}
    errors: list[str] = []
    all_top: list[dict] = []
    captured: dict[str, list[str]] = {}

    for channel in CHANNELS:
        try:
            if args.from_cache:
                posts = fetch_channel_from_cache(channel, cached.get(channel, []))
                captured[channel] = cached.get(channel, [])
            else:
                posts, ds_ids = fetch_channel_from_apify(channel)
                captured[channel] = ds_ids
            top, c = process_channel(channel, posts, start, end)
        except Exception as exc:
            log.error("[%s] failed: %s", channel, exc)
            errors.append(f"{channel}: {exc}")
            counts[channel] = {"raw": 0, "month": 0, "top": 0}
            continue
        counts[channel] = c
        all_top.extend(top)
        for p in top:
            log.info("[%s] TOP @%s · likes=%d views=%d → %s",
                     channel, p.get("creator_handle") or "?",
                     p.get("likes") or 0, p.get("views") or 0,
                     p.get("post_url") or "")

    if not args.from_cache and any(captured.values()):
        save_history(month, captured)
        log.info("Saved dataset history → %s", history_path(month))

    if args.dry_run:
        log.info("Dry run — skipping DB insert and email. Re-run with --from-cache for free recovery.")
        return 0

    log.info("Inserting %d posts under week_id=%s", len(all_top), month)
    db.insert_week(month, all_top)

    subject = f"Content Hub: {month} digest ready" + (f" ({len(errors)} errors)" if errors else "")
    send_status_email(subject, build_status_html(month, counts, errors, used, cap))
    log.info("Done. View at http://localhost:4000/week/%s", month)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        traceback.print_exc()
        sys.exit(1)
