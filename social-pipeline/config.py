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
