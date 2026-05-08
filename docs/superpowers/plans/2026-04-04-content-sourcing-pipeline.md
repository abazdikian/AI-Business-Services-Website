# Content Sourcing Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an automated pipeline that fetches AI news weekly, drafts social media captions with Hormozi-style hooks, and emails a branded HTML digest to Alice every Sunday at 9am ET.

**Architecture:** Python scripts in a `social-pipeline/` directory. Each step (fetch, draft, format, send) is a separate module. An orchestrator (`run_pipeline.py`) calls them in sequence. Gmail API auth reuses the OAuth pattern from the AL Pro project. Claude API handles content curation and caption drafting.

**Tech Stack:** Python 3, requests, feedparser (RSS), anthropic SDK, google-auth + google-api-python-client (Gmail API), MIMEText + base64 (email construction).

**Spec:** `docs/superpowers/specs/2026-04-04-content-sourcing-pipeline-design.md`

---

## File Structure

```
social-pipeline/
├── config.py              # Constants: email, URLs, category mix
├── gmail_auth.py          # Gmail OAuth (local files or env vars)
├── fetch_reddit.py        # Fetch r/ClaudeAI + r/anthropic top posts
├── fetch_anthropic.py     # Fetch Anthropic blog/news page
├── fetch_news.py          # Fetch AI news from RSS feeds
├── draft_posts.py         # Claude API drafts captions + hashtags
├── format_email.py        # Render branded HTML digest
├── send_email.py          # Gmail API send
├── run_pipeline.py        # Orchestrator
├── last_run.json          # Timestamp state
└── requirements.txt       # Dependencies
```

---

### Task 1: Project setup and config

**Files:**
- Create: `social-pipeline/config.py`
- Create: `social-pipeline/requirements.txt`
- Create: `social-pipeline/last_run.json`

- [ ] **Step 1: Create the social-pipeline directory**

```bash
mkdir -p "/Users/alicebazidian/Desktop/AI Project/AI Services Website/social-pipeline"
```

- [ ] **Step 2: Create requirements.txt**

```
requests>=2.31.0
feedparser>=6.0.0
anthropic>=0.40.0
google-auth>=2.25.0
google-auth-oauthlib>=1.2.0
google-api-python-client>=2.110.0
```

- [ ] **Step 3: Create config.py**

```python
"""
Configuration for the Social Media Content Sourcing Pipeline.
"""

import os

# ── Email ──
ALICE_EMAIL = "alice.b@alprosolutions.ca"

# ── Reddit Sources ──
REDDIT_SUBS = [
    {"name": "ClaudeAI", "url": "https://www.reddit.com/r/ClaudeAI/top.json?t=week&limit=25"},
    {"name": "anthropic", "url": "https://www.reddit.com/r/anthropic/top.json?t=week&limit=25"},
]
REDDIT_MIN_SCORE = 10
REDDIT_HEADERS = {"User-Agent": "SmallBizAICoach/1.0 (content digest)"}

# ── Anthropic Blog ──
ANTHROPIC_NEWS_URL = "https://www.anthropic.com/news"

# ── RSS Feeds ──
RSS_FEEDS = [
    "https://techcrunch.com/category/artificial-intelligence/feed/",
    "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    "https://www.technologyreview.com/feed/",
]

# ── Claude API ──
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = "claude-sonnet-4-6-20250514"

# ── Content Mix Targets ──
CATEGORY_TARGETS = {
    "ai-news": 5,
    "how-to": 3,
    "thought-leadership": 2,
    "engagement": 2,
    "promo": 1,
}
TOTAL_ITEMS_MIN = 10
TOTAL_ITEMS_MAX = 14

# ── Brand ──
BRAND_NAME = "ALICE BAZDIKIAN SMB AI COACH"
WEBSITE_URL = "https://smallbusinessaicoach.com"
HASHTAGS_BRANDED = ["#SmallBusinessAI", "#AliceAI", "#AICoach"]
HASHTAGS_NICHE = ["#ClaudeAI", "#AIforBusiness", "#AIProductivity"]
HASHTAGS_REACH = ["#SmallBusiness", "#Entrepreneur", "#WomenInBusiness"]

# ── Paths ──
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LAST_RUN_FILE = os.path.join(BASE_DIR, "last_run.json")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
```

- [ ] **Step 4: Create last_run.json**

```json
{"last_run": null}
```

- [ ] **Step 5: Install dependencies**

```bash
cd "/Users/alicebazidian/Desktop/AI Project/AI Services Website/social-pipeline"
pip3 install -r requirements.txt
```

- [ ] **Step 6: Commit**

```bash
git add social-pipeline/
git commit -m "feat: add social-pipeline project setup and config"
```

---

### Task 2: Reddit fetcher

**Files:**
- Create: `social-pipeline/fetch_reddit.py`

- [ ] **Step 1: Create fetch_reddit.py**

```python
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

            # Be polite to Reddit
            time.sleep(1)

        except Exception as e:
            print(f"[WARN] Failed to fetch r/{sub['name']}: {e}")
            continue

    # Sort by score descending
    stories.sort(key=lambda s: s["score"], reverse=True)
    print(f"[Reddit] Fetched {len(stories)} posts")
    return stories


if __name__ == "__main__":
    results = fetch_reddit()
    for s in results[:5]:
        print(f"  [{s['score']}] {s['title']}")
```

- [ ] **Step 2: Test it**

```bash
cd "/Users/alicebazidian/Desktop/AI Project/AI Services Website/social-pipeline"
python3 fetch_reddit.py
```

Expected: prints 5+ post titles with scores from r/ClaudeAI and r/anthropic.

- [ ] **Step 3: Commit**

```bash
git add social-pipeline/fetch_reddit.py
git commit -m "feat: add Reddit fetcher for content pipeline"
```

---

### Task 3: Anthropic blog fetcher

**Files:**
- Create: `social-pipeline/fetch_anthropic.py`

- [ ] **Step 1: Create fetch_anthropic.py**

```python
"""
Fetch recent posts from Anthropic's news/blog page.
Parses the HTML to extract post titles, URLs, and dates.
"""

import requests
import re
import json
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

        # Anthropic's news page uses JSON data embedded in the page
        # Look for article links and titles in the HTML
        # Pattern: <a href="/news/...">...</a> with title text
        link_pattern = re.findall(
            r'href="(/news/[^"]+)"[^>]*>([^<]+)</a>',
            html
        )

        # Also try the /research pattern
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

        # Try to fetch each post page to get a description
        for story in stories[:10]:
            try:
                page = requests.get(story["url"], timeout=10, headers={
                    "User-Agent": "SmallBizAICoach/1.0 (content digest)"
                })
                # Extract meta description
                desc_match = re.search(
                    r'<meta\s+name="description"\s+content="([^"]*)"',
                    page.text
                )
                if desc_match:
                    story["body"] = desc_match.group(1)[:500]

                # Extract publish date if available
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

        # Remove old posts
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
```

- [ ] **Step 2: Test it**

```bash
cd "/Users/alicebazidian/Desktop/AI Project/AI Services Website/social-pipeline"
python3 fetch_anthropic.py
```

Expected: prints recent Anthropic blog post titles.

- [ ] **Step 3: Commit**

```bash
git add social-pipeline/fetch_anthropic.py
git commit -m "feat: add Anthropic blog fetcher for content pipeline"
```

---

### Task 4: RSS news fetcher

**Files:**
- Create: `social-pipeline/fetch_news.py`

- [ ] **Step 1: Create fetch_news.py**

```python
"""
Fetch AI news from RSS feeds (TechCrunch AI, The Verge AI, MIT Tech Review).
"""

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
                # Parse publish date
                pub_date = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    pub_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                    pub_date = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)

                if pub_date and pub_date < cutoff:
                    continue

                # Get summary/description
                body = ""
                if hasattr(entry, "summary"):
                    # Strip HTML tags from summary
                    import re
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
```

- [ ] **Step 2: Test it**

```bash
cd "/Users/alicebazidian/Desktop/AI Project/AI Services Website/social-pipeline"
python3 fetch_news.py
```

Expected: prints 5+ article titles from TechCrunch/Verge/MIT Tech Review RSS feeds.

- [ ] **Step 3: Commit**

```bash
git add social-pipeline/fetch_news.py
git commit -m "feat: add RSS news fetcher for content pipeline"
```

---

### Task 5: Claude API content drafter

**Files:**
- Create: `social-pipeline/draft_posts.py`

- [ ] **Step 1: Create draft_posts.py**

```python
"""
Use Claude API to curate raw stories into 10-14 post-ready items
with Hormozi-style captions and hashtags.
"""

import json
import anthropic
from config import (
    ANTHROPIC_API_KEY, CLAUDE_MODEL,
    TOTAL_ITEMS_MIN, TOTAL_ITEMS_MAX,
    HASHTAGS_BRANDED, HASHTAGS_NICHE, HASHTAGS_REACH,
    WEBSITE_URL,
)

SYSTEM_PROMPT = """You are a social media content strategist for Alice Bazdikian, a small business AI coach.

Your job: take raw AI news stories and turn them into social media post drafts.

BRAND VOICE:
- Friendly + authoritative. Like a smart friend who happens to be an expert.
- Hormozi-style hooks: punchy, contrarian, numbers-driven opening lines.
- Target audience: small business owners, especially women.
- Never use jargon. Never hype. Never generic.
- Include specific numbers and actionable steps when possible.

CAPTION STRUCTURE:
1. Hook line (bold, attention-grabbing, Hormozi-style)
2. 3-5 value bullets using → arrows
3. One-line CTA (e.g., "Save this for later", "Which one are you using?", "Link in bio for the full guide")

CONTENT CATEGORIES — assign each item one of:
- "ai-news": Breaking AI news relevant to small business owners
- "how-to": Practical tip or tutorial derived from the news
- "thought-leadership": Hot take, contrarian angle, or industry insight
- "engagement": Poll question, discussion prompt, or "which would you choose?"
- "promo": Tie the news to Alice's coaching, workshops, or scorecard (website: smallbusinessaicoach.com)

HASHTAGS — for each post, provide:
- branded: from ["#SmallBusinessAI", "#AliceAI", "#AICoach"]
- niche: from ["#ClaudeAI", "#AIforBusiness", "#AIProductivity"]
- reach: from ["#SmallBusiness", "#Entrepreneur", "#WomenInBusiness"]
Pick 2-3 from each tier (6-9 total per post).

OUTPUT FORMAT: Return valid JSON — an array of objects, each with:
{
  "headline": "short punchy headline",
  "summary": "2-3 sentence summary of the story",
  "caption": "the full social media caption",
  "hashtags": {"branded": [...], "niche": [...], "reach": [...]},
  "source_url": "original URL",
  "category": "one of the 5 categories"
}

Return EXACTLY between """ + str(TOTAL_ITEMS_MIN) + " and " + str(TOTAL_ITEMS_MAX) + """ items.
Prioritize the most interesting, actionable, and relevant stories for small business owners.
Skip stories that are too technical, too niche, or not relevant to the audience."""


def draft_posts(raw_stories):
    """Take raw stories and produce curated, draft-ready post items via Claude API."""
    if not ANTHROPIC_API_KEY:
        print("[ERROR] ANTHROPIC_API_KEY not set")
        return []

    # Build the user message with all raw stories
    stories_text = json.dumps(raw_stories, indent=2)
    user_message = f"""Here are {len(raw_stories)} raw AI news stories from this week.

Curate the best ones and draft social media posts for each.

RAW STORIES:
{stories_text}"""

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    try:
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=8000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )

        # Extract JSON from response
        response_text = response.content[0].text

        # Try to parse JSON directly, or extract from code block
        try:
            items = json.loads(response_text)
        except json.JSONDecodeError:
            # Look for JSON array in code block
            import re
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                items = json.loads(json_match.group())
            else:
                print("[ERROR] Could not parse Claude response as JSON")
                print(response_text[:500])
                return []

        print(f"[Draft] Generated {len(items)} post drafts")
        return items

    except Exception as e:
        print(f"[ERROR] Claude API failed: {e}")
        return []


if __name__ == "__main__":
    # Test with sample data
    sample = [
        {
            "source": "reddit/r/ClaudeAI",
            "title": "Claude Code now supports parallel sub-agents",
            "body": "You can dispatch multiple agents to work on different tasks simultaneously.",
            "url": "https://reddit.com/r/ClaudeAI/example",
            "score": 150,
            "comments": 45,
            "created": 0,
        },
        {
            "source": "anthropic-blog",
            "title": "Introducing Claude 4.5 Haiku",
            "body": "Our fastest model yet, now available to all users.",
            "url": "https://anthropic.com/news/claude-4-5-haiku",
            "score": 0,
            "comments": 0,
            "created": 0,
        },
    ]
    results = draft_posts(sample)
    for item in results:
        print(f"\n[{item.get('category')}] {item.get('headline')}")
        print(f"  Caption: {item.get('caption', '')[:100]}...")
```

- [ ] **Step 2: Test it (requires ANTHROPIC_API_KEY)**

```bash
cd "/Users/alicebazidian/Desktop/AI Project/AI Services Website/social-pipeline"
ANTHROPIC_API_KEY="your-key-here" python3 draft_posts.py
```

Expected: prints 2 drafted items with headlines, categories, and caption previews.

- [ ] **Step 3: Commit**

```bash
git add social-pipeline/draft_posts.py
git commit -m "feat: add Claude API content drafter for pipeline"
```

---

### Task 6: HTML email formatter

**Files:**
- Create: `social-pipeline/format_email.py`

- [ ] **Step 1: Create format_email.py**

```python
"""
Render drafted posts into a branded HTML digest email.
"""

from datetime import datetime
from config import BRAND_NAME, WEBSITE_URL


CATEGORY_LABELS = {
    "ai-news": "AI News",
    "how-to": "How-To",
    "thought-leadership": "Hot Take",
    "engagement": "Engagement",
    "promo": "Your Business",
}

CATEGORY_COLORS = {
    "ai-news": "#7D2240",
    "how-to": "#C9A847",
    "thought-leadership": "#651B33",
    "engagement": "#6B6560",
    "promo": "#B8952E",
}


def format_email(items):
    """Render a list of drafted post items into a branded HTML email string."""
    date_str = datetime.now().strftime("%B %d, %Y")

    cards_html = ""
    for i, item in enumerate(items):
        cat = item.get("category", "ai-news")
        cat_label = CATEGORY_LABELS.get(cat, cat)
        cat_color = CATEGORY_COLORS.get(cat, "#7D2240")

        # Format hashtags
        hashtags = item.get("hashtags", {})
        all_tags = hashtags.get("branded", []) + hashtags.get("niche", []) + hashtags.get("reach", [])
        tags_str = " ".join(all_tags)

        # Escape caption for HTML (preserve newlines)
        caption = item.get("caption", "")
        caption_html = caption.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")

        cards_html += f"""
        <tr><td style="padding:0 0 24px 0;">
          <table width="100%" cellpadding="0" cellspacing="0" style="background:#FFFFFF;border-radius:12px;border:1px solid rgba(28,28,28,0.09);overflow:hidden;">
            <tr><td style="padding:24px 28px;">
              <span style="display:inline-block;background:{cat_color};color:#F7F3EE;font-size:11px;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;padding:4px 12px;border-radius:100px;margin-bottom:12px;">{cat_label}</span>
              <h2 style="font-family:Georgia,'Playfair Display',serif;font-size:20px;font-weight:700;color:#1C1C1C;margin:12px 0 8px;line-height:1.3;">{item.get('headline', '')}</h2>
              <p style="font-size:14px;color:#6B6560;line-height:1.6;margin:0 0 16px;">{item.get('summary', '')}</p>
              <div style="background:rgba(125,34,64,0.04);border-left:3px solid #C9A847;border-radius:0 8px 8px 0;padding:14px 18px;margin:0 0 14px;">
                <p style="font-size:11px;font-weight:700;color:#C9A847;letter-spacing:0.08em;text-transform:uppercase;margin:0 0 6px;">Draft Caption</p>
                <p style="font-size:13px;color:#1C1C1C;line-height:1.65;margin:0;">{caption_html}</p>
              </div>
              <p style="font-size:12px;color:#6B6560;margin:0 0 8px;">{tags_str}</p>
              <a href="{item.get('source_url', '#')}" style="font-size:12px;color:#7D2240;font-weight:600;text-decoration:none;">View source &rarr;</a>
            </td></tr>
          </table>
        </td></tr>"""

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#F7F3EE;font-family:Arial,'Inter',sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#F7F3EE;">
    <tr><td align="center" style="padding:32px 16px;">
      <table width="100%" cellpadding="0" cellspacing="0" style="max-width:620px;">

        <!-- Header -->
        <tr><td style="text-align:center;padding:0 0 32px;">
          <p style="font-family:Georgia,'Playfair Display',serif;font-size:24px;font-weight:700;color:#7D2240;margin:0 0 4px;">AB</p>
          <h1 style="font-family:Georgia,'Playfair Display',serif;font-size:28px;font-weight:700;color:#1C1C1C;margin:0 0 6px;line-height:1.2;">Weekly AI Digest</h1>
          <p style="font-size:13px;color:#6B6560;margin:0;">{date_str} &middot; {len(items)} stories curated for you</p>
        </td></tr>

        <!-- Divider -->
        <tr><td style="padding:0 0 24px;"><div style="height:2px;background:linear-gradient(90deg,#7D2240,#C9A847);border-radius:2px;"></div></td></tr>

        <!-- Cards -->
        {cards_html}

        <!-- Footer -->
        <tr><td style="text-align:center;padding:24px 0 0;border-top:1px solid rgba(28,28,28,0.09);">
          <p style="font-size:14px;color:#1C1C1C;font-weight:600;margin:0 0 4px;">Reply with your picks for the week</p>
          <p style="font-size:12px;color:#6B6560;margin:0 0 16px;">Just reply with the numbers (e.g., "1, 3, 5, 8") and I'll prep them.</p>
          <p style="font-size:11px;color:#b0a8a0;margin:0;">{BRAND_NAME} &middot; <a href="{WEBSITE_URL}" style="color:#7D2240;text-decoration:none;">{WEBSITE_URL}</a></p>
        </td></tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""

    return html


if __name__ == "__main__":
    # Test with sample data
    sample_items = [
        {
            "headline": "Claude Can Now Run Your Calendar",
            "summary": "Anthropic released Claude Connectors, letting Claude access Google Calendar, Slack, and Drive directly.",
            "caption": "Your AI just became your executive assistant.\n\nClaude can now:\n→ Read your calendar\n→ Send Slack messages\n→ Pull files from Drive\n\nThis changes everything for solopreneurs.",
            "hashtags": {"branded": ["#SmallBusinessAI"], "niche": ["#ClaudeAI"], "reach": ["#Entrepreneur"]},
            "source_url": "https://anthropic.com/news/example",
            "category": "ai-news",
        },
        {
            "headline": "Stop Using AI Like Google",
            "summary": "Most business owners treat AI as a search engine. Here's why that's wasting 90% of its potential.",
            "caption": "Everyone's using Claude wrong.\n\nThey type a question. Get an answer. Close the tab.\n\nThat's like hiring an employee and only asking them for directions.\n\nHere's what the top 1% do instead →",
            "hashtags": {"branded": ["#AliceAI"], "niche": ["#AIforBusiness"], "reach": ["#WomenInBusiness"]},
            "source_url": "https://reddit.com/r/ClaudeAI/example",
            "category": "thought-leadership",
        },
    ]

    html = format_email(sample_items)
    with open("output/test-digest.html", "w") as f:
        f.write(html)
    print(f"[Format] Test digest written to output/test-digest.html ({len(html)} bytes)")
```

- [ ] **Step 2: Create output directory and test**

```bash
cd "/Users/alicebazidian/Desktop/AI Project/AI Services Website/social-pipeline"
mkdir -p output
python3 format_email.py
```

Expected: creates `output/test-digest.html`. Open in browser to verify branded layout.

- [ ] **Step 3: Commit**

```bash
git add social-pipeline/format_email.py
git commit -m "feat: add branded HTML email formatter for digest"
```

---

### Task 7: Gmail sender

**Files:**
- Create: `social-pipeline/gmail_auth.py`
- Create: `social-pipeline/send_email.py`

- [ ] **Step 1: Create gmail_auth.py (dual-source: local files or env vars)**

```python
"""
Gmail API Authentication — supports local files or environment variables.

Local: reads credentials.json + token.json from this directory.
Remote: reads GMAIL_CREDENTIALS_JSON + GMAIL_TOKEN_JSON env vars.
"""

import os
import json
import tempfile
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_FILE = os.path.join(BASE_DIR, "credentials.json")
TOKEN_FILE = os.path.join(BASE_DIR, "token.json")

SCOPES = [
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.modify",
]


def get_gmail_service():
    """Return an authenticated Gmail API service instance."""
    creds = None

    # Try env vars first (for remote/scheduled execution)
    token_json_env = os.environ.get("GMAIL_TOKEN_JSON")
    if token_json_env:
        token_data = json.loads(token_json_env)
        creds = Credentials.from_authorized_user_info(token_data, SCOPES)
    elif os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            # Save refreshed token
            if token_json_env:
                print("[AUTH] Token refreshed (env var mode — update GMAIL_TOKEN_JSON with new token)")
            else:
                with open(TOKEN_FILE, "w") as f:
                    f.write(creds.to_json())
        else:
            # Need fresh auth — only works locally
            creds_json_env = os.environ.get("GMAIL_CREDENTIALS_JSON")
            if creds_json_env:
                # Write to temp file for the flow
                tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
                tmp.write(creds_json_env)
                tmp.close()
                creds_file = tmp.name
            elif os.path.exists(CREDENTIALS_FILE):
                creds_file = CREDENTIALS_FILE
            else:
                raise FileNotFoundError(
                    f"No credentials found. Set GMAIL_CREDENTIALS_JSON env var "
                    f"or place credentials.json in {BASE_DIR}"
                )

            flow = InstalledAppFlow.from_client_secrets_file(creds_file, SCOPES)
            creds = flow.run_local_server(port=0)

            if not token_json_env:
                with open(TOKEN_FILE, "w") as f:
                    f.write(creds.to_json())
                print(f"[AUTH] Token saved to {TOKEN_FILE}")

    return build("gmail", "v1", credentials=creds)


if __name__ == "__main__":
    print("Authenticating with Gmail API...")
    service = get_gmail_service()
    profile = service.users().getProfile(userId="me").execute()
    print(f"Authenticated as: {profile['emailAddress']}")
    print("Gmail API connection successful!")
```

- [ ] **Step 2: Copy credentials from AL Pro project**

```bash
cp "/Users/alicebazidian/Desktop/AL Pro Solar Sales Funnel /credentials.json" "/Users/alicebazidian/Desktop/AI Project/AI Services Website/social-pipeline/credentials.json"
cp "/Users/alicebazidian/Desktop/AL Pro Solar Sales Funnel /token.json" "/Users/alicebazidian/Desktop/AI Project/AI Services Website/social-pipeline/token.json"
```

- [ ] **Step 3: Test auth**

```bash
cd "/Users/alicebazidian/Desktop/AI Project/AI Services Website/social-pipeline"
python3 gmail_auth.py
```

Expected: "Authenticated as: alice.b@alprosolutions.ca"

- [ ] **Step 4: Create send_email.py**

```python
"""
Send an HTML email via Gmail API.
"""

import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import ALICE_EMAIL
from gmail_auth import get_gmail_service


def send_email(subject, html_body):
    """Send an HTML email to Alice via Gmail API."""
    service = get_gmail_service()

    msg = MIMEMultipart("alternative")
    msg["to"] = ALICE_EMAIL
    msg["from"] = ALICE_EMAIL
    msg["subject"] = subject

    # Plain text fallback
    plain = "Your weekly AI digest is ready. View this email in HTML mode for the full experience."
    msg.attach(MIMEText(plain, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
    sent = service.users().messages().send(
        userId="me", body={"raw": raw}
    ).execute()

    print(f"[Send] Email sent — Message ID: {sent['id']}")
    return sent["id"]


if __name__ == "__main__":
    test_html = """
    <html><body style="font-family:Arial;padding:20px;">
    <h1 style="color:#7D2240;">Test Digest Email</h1>
    <p>If you see this, the Gmail API send is working!</p>
    </body></html>
    """
    send_email("Test — Social Pipeline Digest", test_html)
    print("Test email sent successfully!")
```

- [ ] **Step 5: Test sending (sends a real test email)**

```bash
cd "/Users/alicebazidian/Desktop/AI Project/AI Services Website/social-pipeline"
python3 send_email.py
```

Expected: "Test email sent successfully!" and a test email appears in Alice's inbox.

- [ ] **Step 6: Add credentials to .gitignore**

Add these lines to the project root `.gitignore`:

```
social-pipeline/credentials.json
social-pipeline/token.json
```

- [ ] **Step 7: Commit**

```bash
git add social-pipeline/gmail_auth.py social-pipeline/send_email.py .gitignore
git commit -m "feat: add Gmail API auth and email sender"
```

---

### Task 8: Pipeline orchestrator

**Files:**
- Create: `social-pipeline/run_pipeline.py`

- [ ] **Step 1: Create run_pipeline.py**

```python
"""
Content Sourcing Pipeline — Orchestrator
Runs all steps in sequence: fetch → dedupe → draft → format → send.
"""

import json
import os
from datetime import datetime, timezone

from config import LAST_RUN_FILE, OUTPUT_DIR, TOTAL_ITEMS_MIN
from fetch_reddit import fetch_reddit
from fetch_anthropic import fetch_anthropic
from fetch_news import fetch_news
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

    all_stories = reddit_stories + anthropic_stories + news_stories
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
        send_email(subject, html)
    except Exception as e:
        print(f"[ERROR] Email send failed: {e}")
        print(f"[FALLBACK] Digest saved locally at {output_path}")
        return

    # Step 6: Update last run
    save_last_run()

    print("\n" + "=" * 60)
    print(f"DONE — {len(drafted_items)} items sent to inbox")
    print("=" * 60)


if __name__ == "__main__":
    run()
```

- [ ] **Step 2: Test the full pipeline**

```bash
cd "/Users/alicebazidian/Desktop/AI Project/AI Services Website/social-pipeline"
ANTHROPIC_API_KEY="your-key-here" python3 run_pipeline.py
```

Expected: fetches from all 3 sources, drafts 10-14 items, sends branded HTML digest to inbox.

- [ ] **Step 3: Commit**

```bash
git add social-pipeline/run_pipeline.py
git commit -m "feat: add pipeline orchestrator — full end-to-end content sourcing"
```

---

### Task 9: Set up scheduled trigger

**Files:**
- No files — uses Claude Code `schedule` skill

- [ ] **Step 1: Set up the Claude Code scheduled trigger**

Use the `schedule` skill to create a remote trigger:
- **Name:** `weekly-ai-digest`
- **Schedule:** Every Sunday at 9:00 AM ET (cron: `0 9 * * 0` in America/New_York)
- **Prompt:** `Run the content sourcing pipeline at /Users/alicebazidian/Desktop/AI Project/AI Services Website/social-pipeline/run_pipeline.py — fetch AI news, draft social posts, and email the digest.`
- **Environment variables:** `ANTHROPIC_API_KEY`, `GMAIL_TOKEN_JSON`, `GMAIL_CREDENTIALS_JSON`

- [ ] **Step 2: Extract Gmail credentials for env vars**

Read `token.json` and `credentials.json` contents and set them as environment variables for the scheduled trigger:

```bash
cd "/Users/alicebazidian/Desktop/AI Project/AI Services Website/social-pipeline"
cat token.json      # Copy this value → set as GMAIL_TOKEN_JSON
cat credentials.json # Copy this value → set as GMAIL_CREDENTIALS_JSON
```

- [ ] **Step 3: Verify the trigger is registered**

List scheduled triggers to confirm `weekly-ai-digest` appears with correct schedule.

- [ ] **Step 4: Commit any final changes**

```bash
git add -A
git commit -m "feat: complete content sourcing pipeline with scheduled trigger"
```
