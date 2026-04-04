"""
Fetch top posts from r/ClaudeAI and r/anthropic for the past week.
Returns a list of story dicts.
"""

import requests
import time
from config import REDDIT_SUBS, REDDIT_MIN_SCORE, REDDIT_HEADERS


def fetch_reddit():
    """Fetch top weekly posts from configured subreddits."""
    stories = []

    for sub in REDDIT_SUBS:
        try:
            resp = requests.get(sub["url"], headers=REDDIT_HEADERS, timeout=15)
            resp.raise_for_status()
            data = resp.json()

            for post in data.get("data", {}).get("children", []):
                p = post["data"]
                if p.get("score", 0) < REDDIT_MIN_SCORE:
                    continue
                if p.get("stickied"):
                    continue

                stories.append({
                    "source": f"reddit/r/{sub['name']}",
                    "title": p.get("title", ""),
                    "body": (p.get("selftext", "") or "")[:500],
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
