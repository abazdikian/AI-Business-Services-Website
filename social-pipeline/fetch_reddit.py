"""
Fetch top posts from r/ClaudeAI and r/anthropic for the past week.
Returns a list of story dicts.
"""

import requests
import time
from config import REDDIT_SUBS, REDDIT_MIN_SCORE, REDDIT_HEADERS, REDDIT_MIN_TITLE_LEN


def fetch_reddit():
    """Fetch top weekly posts from configured subreddits."""
    stories = []

    for sub in REDDIT_SUBS:
        min_score = sub.get("min_score", REDDIT_MIN_SCORE)
        try:
            resp = requests.get(sub["url"], headers=REDDIT_HEADERS, timeout=15)
            resp.raise_for_status()
            data = resp.json()

            for post in data.get("data", {}).get("children", []):
                p = post["data"]
                if p.get("score", 0) < min_score:
                    continue
                if p.get("stickied"):
                    continue
                # Skip meme/image-only posts — require meaningful title
                title = p.get("title", "")
                if len(title) < REDDIT_MIN_TITLE_LEN:
                    continue
                # Skip image-only posts with no text body
                body = (p.get("selftext", "") or "").strip()
                is_link = p.get("is_self") is False
                if not body and not is_link:
                    continue

                stories.append({
                    "source": f"reddit/r/{sub['name']}",
                    "title": title,
                    "body": body[:500],
                    "url": f"https://www.reddit.com{p.get('permalink', '')}",
                    "score": p.get("score", 0),
                    "comments": p.get("num_comments", 0),
                    "created": p.get("created_utc", 0),
                })

            time.sleep(1)

        except Exception as e:
            print(f"[WARN] Failed to fetch r/{sub['name']}: {e}")
            continue

    stories.sort(key=lambda s: s["score"], reverse=True)
    print(f"[Reddit] Fetched {len(stories)} posts")
    return stories


if __name__ == "__main__":
    results = fetch_reddit()
    for s in results[:5]:
        print(f"  [{s['score']}] {s['title']}")
