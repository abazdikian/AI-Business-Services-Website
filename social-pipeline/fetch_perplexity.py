"""
Fetch AI + small business insights via Perplexity API (sonar model).
Returns stories with citations for the weekly digest.
"""

import os
import json
import requests
from config import PERPLEXITY_API_KEY, PERPLEXITY_MODEL, PERPLEXITY_QUERIES

API_URL = "https://api.perplexity.ai/chat/completions"


def _query_perplexity(query):
    """Run a single Perplexity search query and extract stories."""
    api_key = PERPLEXITY_API_KEY or os.environ.get("PERPLEXITY_API_KEY", "")
    if not api_key:
        print("[WARN] PERPLEXITY_API_KEY not set — skipping Perplexity")
        return []

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": PERPLEXITY_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a research assistant for an AI coaching business targeting "
                    "women small business owners and solopreneurs. Find the most actionable, "
                    "specific, and recent stories. Focus on real examples with numbers, "
                    "dollar amounts, or time savings. Skip corporate AI news, policy, "
                    "and developer-only content."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"{query}\n\n"
                    "Return exactly 3-5 items as a JSON array. Each item:\n"
                    '{"title": "headline max 12 words", "body": "2-3 sentence summary '
                    'with specific numbers/results", "url": "source URL"}\n\n'
                    "Return ONLY the JSON array, no other text."
                ),
            },
        ],
        "max_tokens": 2000,
        "temperature": 0.3,
    }

    try:
        resp = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        content = data["choices"][0]["message"]["content"]
        citations = data.get("citations", [])

        # Parse the JSON from the response
        try:
            items = json.loads(content)
        except json.JSONDecodeError:
            # Try to extract JSON array from the response
            import re
            match = re.search(r'\[.*\]', content, re.DOTALL)
            if match:
                items = json.loads(match.group())
            else:
                print(f"[WARN] Could not parse Perplexity response for: {query[:50]}")
                return []

        stories = []
        for i, item in enumerate(items):
            # Skip non-dict items (sometimes Perplexity returns strings)
            if not isinstance(item, dict):
                continue

            url = item.get("url", "")
            # If no URL in item, use citation if available
            if not url and citations and i < len(citations):
                url = citations[i]

            stories.append({
                "source": "perplexity",
                "title": item.get("title", ""),
                "body": item.get("body", ""),
                "url": url,
                "score": 0,
                "comments": 0,
                "created": 0,
            })

        return stories

    except Exception as e:
        print(f"[WARN] Perplexity query failed ({query[:40]}...): {e}")
        return []


def fetch_perplexity():
    """Run all configured Perplexity queries and return combined stories."""
    all_stories = []
    seen_titles = set()

    for query in PERPLEXITY_QUERIES:
        results = _query_perplexity(query)
        for story in results:
            # Dedupe by title similarity
            title_key = story["title"].lower().strip()[:50]
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                all_stories.append(story)

    print(f"[Perplexity] Fetched {len(all_stories)} insights")
    return all_stories


if __name__ == "__main__":
    from dotenv import load_dotenv
    import sys
    # Load .env from parent directory
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    load_dotenv(env_path)

    results = fetch_perplexity()
    for s in results:
        print(f"\n  {s['title']}")
        print(f"    {s['body'][:120]}...")
        if s['url']:
            print(f"    {s['url']}")
