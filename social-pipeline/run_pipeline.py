"""
Content Sourcing Pipeline — Orchestrator
Runs all steps in sequence: fetch → dedupe → draft → format → send.
"""

import json
import os
from datetime import datetime, timezone

from config import LAST_RUN_FILE, OUTPUT_DIR, TOTAL_ITEMS_MIN, DIGEST_DATA_DIR, LATEST_DIGEST_FILE, LAST_THREAD_FILE
from fetch_reddit import fetch_reddit
from fetch_anthropic import fetch_anthropic
from fetch_news import fetch_news
from fetch_perplexity import fetch_perplexity
from draft_posts import draft_posts
from format_email import format_email
from send_email import send_email


def load_last_run():
    """Load the last run timestamp."""
    try:
        with open(LAST_RUN_FILE) as f:
            data = json.load(f)
            return data.get("last_run")
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def save_last_run():
    """Save the current timestamp as last run."""
    with open(LAST_RUN_FILE, "w") as f:
        json.dump({"last_run": datetime.now(timezone.utc).isoformat()}, f)


def dedupe_stories(stories):
    """Remove duplicate stories based on URL similarity and title overlap."""
    seen_urls = set()
    seen_titles = set()
    unique = []

    for story in stories:
        url = story.get("url", "").rstrip("/").lower()
        title_key = story.get("title", "").lower().strip()[:60]

        if url in seen_urls or title_key in seen_titles:
            continue

        seen_urls.add(url)
        seen_titles.add(title_key)
        unique.append(story)

    removed = len(stories) - len(unique)
    if removed > 0:
        print(f"[Dedupe] Removed {removed} duplicates, {len(unique)} unique stories remain")
    return unique


def run():
    """Run the full content sourcing pipeline."""
    print("=" * 60)
    print(f"Content Sourcing Pipeline — {datetime.now().strftime('%B %d, %Y %I:%M %p')}")
    print("=" * 60)

    # Step 1: Fetch from all sources
    print("\n--- FETCHING ---")
    reddit_stories = fetch_reddit()
    anthropic_stories = fetch_anthropic()
    news_stories = fetch_news()
    perplexity_stories = fetch_perplexity()

    all_stories = reddit_stories + anthropic_stories + news_stories + perplexity_stories
    print(f"\nTotal raw stories: {len(all_stories)}")

    if len(all_stories) == 0:
        print("[ERROR] No stories fetched from any source. Aborting.")
        return

    # Step 2: Deduplicate
    print("\n--- DEDUPLICATION ---")
    unique_stories = dedupe_stories(all_stories)

    # Step 3: Draft posts via Claude API
    print("\n--- DRAFTING ---")
    drafted_items = draft_posts(unique_stories)

    if not drafted_items:
        # Fallback: send raw stories without captions
        print("[WARN] Drafting failed — sending raw stories as fallback")
        drafted_items = [
            {
                "headline": s["title"],
                "summary": s.get("body", "")[:200],
                "caption": "(Draft unavailable — Claude API issue)",
                "hashtags": {"branded": [], "niche": [], "reach": []},
                "source_url": s["url"],
                "category": "ai-news",
            }
            for s in unique_stories[:14]
        ]

    # Step 4: Format HTML email
    print("\n--- FORMATTING ---")
    html = format_email(drafted_items)

    # Save a local copy
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    date_slug = datetime.now().strftime("%Y-%m-%d")
    output_path = os.path.join(OUTPUT_DIR, f"digest-{date_slug}.html")
    with open(output_path, "w") as f:
        f.write(html)
    print(f"[Format] Saved local copy to {output_path}")

    # Step 5: Send email
    print("\n--- SENDING ---")
    light_week = len(drafted_items) < TOTAL_ITEMS_MIN
    subject = f"Weekly AI Digest — {datetime.now().strftime('%B %d, %Y')}"
    if light_week:
        subject += " (Light week)"

    try:
        msg_id, thread_id = send_email(subject, html)
    except Exception as e:
        print(f"[ERROR] Email send failed: {e}")
        print(f"[FALLBACK] Digest saved locally at {output_path}")
        return

    # Step 6: Save digest data for template generation
    os.makedirs(DIGEST_DATA_DIR, exist_ok=True)
    with open(LATEST_DIGEST_FILE, "w") as f:
        json.dump(drafted_items, f, indent=2)
    print(f"[Data] Saved {len(drafted_items)} items to {LATEST_DIGEST_FILE}")

    with open(LAST_THREAD_FILE, "w") as f:
        f.write(thread_id)
    print(f"[Data] Thread ID saved: {thread_id}")

    # Step 7: Update last run
    save_last_run()

    print("\n" + "=" * 60)
    print(f"DONE — {len(drafted_items)} items sent to inbox")
    print("=" * 60)


if __name__ == "__main__":
    run()
