"""
Fetch AI news from RSS feeds (TechCrunch AI, The Verge AI, MIT Tech Review).
"""

import re
import feedparser
from datetime import datetime, timedelta, timezone
from config import RSS_FEEDS


def fetch_news(since_days=7):
    """Fetch AI news articles from RSS feeds published in the last `since_days` days."""
    stories = []
    cutoff = datetime.now(timezone.utc) - timedelta(days=since_days)

    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            feed_name = feed.feed.get("title", feed_url)

            for entry in feed.entries[:20]:
                pub_date = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    pub_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                    pub_date = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)

                if pub_date and pub_date < cutoff:
                    continue

                body = ""
                if hasattr(entry, "summary"):
                    body = re.sub(r"<[^>]+>", "", entry.summary)[:500]

                stories.append({
                    "source": f"rss/{feed_name}",
                    "title": entry.get("title", ""),
                    "body": body,
                    "url": entry.get("link", ""),
                    "score": 0,
                    "comments": 0,
                    "created": pub_date.timestamp() if pub_date else 0,
                })

        except Exception as e:
            print(f"[WARN] Failed to fetch RSS {feed_url}: {e}")
            continue

    print(f"[RSS] Fetched {len(stories)} articles")
    return stories


if __name__ == "__main__":
    results = fetch_news()
    for s in results[:5]:
        print(f"  [{s['source']}] {s['title']}")
