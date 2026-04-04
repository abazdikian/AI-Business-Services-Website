"""
Fetch recent posts from Anthropic's news/blog page.
"""

import requests
import re
from datetime import datetime, timedelta, timezone
from config import ANTHROPIC_NEWS_URL


def fetch_anthropic(since_days=7):
    """Fetch Anthropic blog posts from the last `since_days` days."""
    stories = []
    cutoff = datetime.now(timezone.utc) - timedelta(days=since_days)

    try:
        resp = requests.get(ANTHROPIC_NEWS_URL, timeout=15, headers={
            "User-Agent": "SmallBizAICoach/1.0 (content digest)"
        })
        resp.raise_for_status()
        html = resp.text

        link_pattern = re.findall(
            r'href="(/news/[^"]+)"[^>]*>([^<]+)</a>',
            html
        )
        research_pattern = re.findall(
            r'href="(/research/[^"]+)"[^>]*>([^<]+)</a>',
            html
        )

        all_links = link_pattern + research_pattern
        seen_urls = set()

        for path, title in all_links:
            title = title.strip()
            if not title or len(title) < 10:
                continue
            full_url = f"https://www.anthropic.com{path}"
            if full_url in seen_urls:
                continue
            seen_urls.add(full_url)

            stories.append({
                "source": "anthropic-blog",
                "title": title,
                "body": "",
                "url": full_url,
                "score": 0,
                "comments": 0,
                "created": 0,
            })

        for story in stories[:10]:
            try:
                page = requests.get(story["url"], timeout=10, headers={
                    "User-Agent": "SmallBizAICoach/1.0 (content digest)"
                })
                desc_match = re.search(
                    r'<meta\s+name="description"\s+content="([^"]*)"',
                    page.text
                )
                if desc_match:
                    story["body"] = desc_match.group(1)[:500]

                date_match = re.search(
                    r'<time[^>]*datetime="([^"]*)"',
                    page.text
                )
                if date_match:
                    try:
                        pub_date = datetime.fromisoformat(date_match.group(1).replace("Z", "+00:00"))
                        if pub_date < cutoff:
                            story["_skip"] = True
                        story["created"] = pub_date.timestamp()
                    except ValueError:
                        pass
            except Exception:
                pass

        stories = [s for s in stories if not s.get("_skip")]

    except Exception as e:
        print(f"[WARN] Failed to fetch Anthropic blog: {e}")

    print(f"[Anthropic] Fetched {len(stories)} posts")
    return stories


if __name__ == "__main__":
    results = fetch_anthropic()
    for s in results[:5]:
        print(f"  {s['title']}")
        if s["body"]:
            print(f"    {s['body'][:100]}...")
