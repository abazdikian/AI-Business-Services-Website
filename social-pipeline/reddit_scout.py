"""
Reddit Scout Agent — Main Orchestrator.

Monitors SMB subreddits hourly for engagement opportunities,
scores posts with Claude, drafts value-first replies, and
delivers them via email.

Usage:
    python reddit_scout.py hourly   # Run hourly scan (during active hours)
    python reddit_scout.py summary  # Run morning summary of warm opportunities
"""

import sys
import os
import json
import time
import requests
from datetime import datetime, timezone, timedelta

# Load .env from parent directory (project root)
try:
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    load_dotenv(env_path)
except ImportError:
    pass

from reddit_scout_config import (
    SCOUT_SUBREDDITS, HOT_THRESHOLD, WARM_THRESHOLD, MAX_POST_AGE_HOURS,
    SEEN_POSTS_TTL_DAYS, ACTIVE_HOURS_START, ACTIVE_HOURS_END,
    REDDIT_HEADERS, REDDIT_MIN_TITLE_LEN,
    SCOUT_DATA_DIR, SEEN_POSTS_FILE, WARM_QUEUE_FILE,
)
from scout_scorer import score_posts, draft_reply
from scout_email import format_hot_alert, format_morning_summary
from send_email import send_email


# ── Data Persistence ──

def _ensure_data_dir():
    os.makedirs(SCOUT_DATA_DIR, exist_ok=True)


def _load_json(filepath, default):
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            return json.load(f)
    return default


def _save_json(filepath, data):
    _ensure_data_dir()
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2, default=str)


def _load_seen_posts():
    return _load_json(SEEN_POSTS_FILE, {})


def _save_seen_posts(seen):
    _save_json(SEEN_POSTS_FILE, seen)


def _load_warm_queue():
    return _load_json(WARM_QUEUE_FILE, [])


def _save_warm_queue(queue):
    _save_json(WARM_QUEUE_FILE, queue)


def _purge_old_seen_posts(seen):
    """Remove seen posts older than TTL."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=SEEN_POSTS_TTL_DAYS)
    cutoff_str = cutoff.isoformat()
    purged = {
        pid: data for pid, data in seen.items()
        if data.get("seen_at", "") > cutoff_str
    }
    removed = len(seen) - len(purged)
    if removed > 0:
        print(f"[Scout] Purged {removed} old entries from seen_posts")
    return purged


# ── Active Hours Check ──

def _is_active_hours():
    """Check if current time is within active scanning hours (Eastern Time)."""
    try:
        from zoneinfo import ZoneInfo
        et = ZoneInfo("America/New_York")
    except ImportError:
        from dateutil.tz import gettz
        et = gettz("America/New_York")

    now_et = datetime.now(et)
    return ACTIVE_HOURS_START <= now_et.hour < ACTIVE_HOURS_END


# ── Reddit Fetching ──

def _fetch_new_posts():
    """Fetch new posts from all scout subreddits."""
    cutoff = time.time() - (MAX_POST_AGE_HOURS * 3600)
    all_posts = []

    for sub in SCOUT_SUBREDDITS:
        try:
            resp = requests.get(sub["url"], headers=REDDIT_HEADERS, timeout=15)
            resp.raise_for_status()
            data = resp.json()

            for child in data.get("data", {}).get("children", []):
                p = child["data"]

                # Skip stickied
                if p.get("stickied"):
                    continue

                # Skip short titles
                title = p.get("title", "")
                if len(title) < REDDIT_MIN_TITLE_LEN:
                    continue

                # Skip image-only posts with no text
                body = (p.get("selftext", "") or "").strip()
                is_link = p.get("is_self") is False
                if not body and not is_link:
                    continue

                created = p.get("created_utc", 0)

                all_posts.append({
                    "post_id": p.get("id", ""),
                    "subreddit": sub["name"],
                    "title": title,
                    "body": body[:500],
                    "permalink": p.get("permalink", ""),
                    "score": p.get("score", 0),
                    "num_comments": p.get("num_comments", 0),
                    "created_utc": created,
                    "is_fresh": created > cutoff,
                })

            time.sleep(1)  # Respect rate limits

        except Exception as e:
            print(f"[Scout] WARN: Failed to fetch r/{sub['name']}: {e}")
            continue

    print(f"[Scout] Fetched {len(all_posts)} posts from {len(SCOUT_SUBREDDITS)} subreddits")
    return all_posts


# ── Hourly Scan ──

def run_hourly():
    """Run the hourly engagement scan."""
    print(f"[Scout] Starting hourly scan at {datetime.now(timezone.utc).isoformat()}")

    # Check active hours
    if not _is_active_hours():
        print("[Scout] Outside active hours — skipping")
        return

    # Fetch new posts
    posts = _fetch_new_posts()
    if not posts:
        print("[Scout] No posts found — done")
        return

    # Deduplicate against seen posts
    seen = _load_seen_posts()
    new_posts = [p for p in posts if p["post_id"] not in seen]
    print(f"[Scout] {len(new_posts)} new posts after dedup (skipped {len(posts) - len(new_posts)} seen)")

    if not new_posts:
        print("[Scout] All posts already seen — done")
        return

    # Score with Claude
    scores = score_posts(new_posts)
    if not scores:
        print("[Scout] Scoring returned no results — done")
        return

    # Build a lookup by post_id
    score_map = {s["post_id"]: s for s in scores}

    hot_posts = []
    warm_posts = []

    for post in new_posts:
        score_data = score_map.get(post["post_id"])
        if not score_data:
            continue

        relevance = score_data.get("relevance_score", 0)
        opp_type = score_data.get("opportunity_type", "skip")

        if opp_type == "skip":
            continue

        if relevance >= HOT_THRESHOLD and post.get("is_fresh", False):
            hot_posts.append({"post": post, "score_data": score_data})
        elif relevance >= WARM_THRESHOLD:
            warm_posts.append({"post": post, "score_data": score_data})

    print(f"[Scout] Classified: {len(hot_posts)} HOT, {len(warm_posts)} WARM")

    # Draft and send hot alerts immediately
    hot_sent = 0
    for item in hot_posts:
        reply = draft_reply(item["post"], item["score_data"])
        if reply:
            subject, html_body = format_hot_alert(item["post"], item["score_data"], reply)
            try:
                send_email(subject, html_body)
                hot_sent += 1
            except Exception as e:
                print(f"[Scout] ERROR sending hot alert: {e}")

    if hot_sent:
        print(f"[Scout] Sent {hot_sent} hot alert emails")

    # Queue warm posts for morning summary
    if warm_posts:
        queue = _load_warm_queue()
        for item in warm_posts:
            queue.append({
                **item["post"],
                "opportunity_type": item["score_data"]["opportunity_type"],
                "relevance_score": item["score_data"]["relevance_score"],
                "reason": item["score_data"]["reason"],
            })
        _save_warm_queue(queue)
        print(f"[Scout] Queued {len(warm_posts)} warm posts for morning summary")

    # Update seen posts
    now_iso = datetime.now(timezone.utc).isoformat()
    for post in new_posts:
        seen[post["post_id"]] = {
            "seen_at": now_iso,
            "subreddit": post["subreddit"],
        }
    seen = _purge_old_seen_posts(seen)
    _save_seen_posts(seen)

    print(f"[Scout] Hourly scan complete — {hot_sent} alerts sent, {len(warm_posts)} queued")


# ── Morning Summary ──

def run_summary():
    """Run the morning summary — draft replies for warm posts and send digest."""
    print(f"[Scout] Starting morning summary at {datetime.now(timezone.utc).isoformat()}")

    queue = _load_warm_queue()
    if not queue:
        print("[Scout] Warm queue is empty — nothing to summarize")
        return

    print(f"[Scout] Processing {len(queue)} warm posts")

    # Draft replies for each queued post
    posts_with_replies = []
    for item in queue:
        score_data = {
            "opportunity_type": item.get("opportunity_type", "help_request"),
            "relevance_score": item.get("relevance_score", 5),
            "reason": item.get("reason", ""),
        }
        reply = draft_reply(item, score_data)
        posts_with_replies.append({
            "post": item,
            "score_data": score_data,
            "draft_reply": reply,
        })

    # Format and send summary
    subject, html_body = format_morning_summary(posts_with_replies)
    if subject and html_body:
        try:
            send_email(subject, html_body)
            print(f"[Scout] Morning summary sent — {len(posts_with_replies)} opportunities")
        except Exception as e:
            print(f"[Scout] ERROR sending summary: {e}")
            return

    # Clear the queue
    _save_warm_queue([])
    print("[Scout] Warm queue cleared")


# ── CLI Entry Point ──

def main():
    if len(sys.argv) < 2:
        print("Usage: python reddit_scout.py [hourly|summary]")
        print("  hourly  — Run hourly engagement scan")
        print("  summary — Run morning summary digest")
        sys.exit(1)

    mode = sys.argv[1].lower()
    if mode == "hourly":
        run_hourly()
    elif mode == "summary":
        run_summary()
    else:
        print(f"Unknown mode: {mode}. Use 'hourly' or 'summary'.")
        sys.exit(1)


if __name__ == "__main__":
    main()
