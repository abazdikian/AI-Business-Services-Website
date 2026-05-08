"""
Configuration for the Social Media Content Sourcing Pipeline.
"""

import os

# ── Email ──
ALICE_EMAIL = "abazdikian@gmail.com"

# ── Reddit Sources ──
REDDIT_SUBS = [
    # AI subs — filter for practical business use cases
    {"name": "ClaudeAI", "url": "https://www.reddit.com/r/ClaudeAI/top.json?t=week&limit=25", "min_score": 50},
    {"name": "ChatGPT", "url": "https://www.reddit.com/r/ChatGPT/top.json?t=week&limit=25", "min_score": 100},
    # SMB + AI intersection subs
    {"name": "smallbusiness", "url": "https://www.reddit.com/r/smallbusiness/top.json?t=week&limit=25", "min_score": 20},
    {"name": "solopreneur", "url": "https://www.reddit.com/r/solopreneur/top.json?t=week&limit=25", "min_score": 15},
    {"name": "EntrepreneurRideAlong", "url": "https://www.reddit.com/r/EntrepreneurRideAlong/top.json?t=week&limit=25", "min_score": 15},
]
REDDIT_MIN_SCORE = 10  # fallback default
# Skip meme/image-only posts — require at least 50 chars of text in title
REDDIT_MIN_TITLE_LEN = 30
REDDIT_HEADERS = {"User-Agent": "SmallBizAICoach/1.0 (content digest)"}

# ── Anthropic Blog ──
ANTHROPIC_NEWS_URL = "https://www.anthropic.com/news"

# ── RSS Feeds ──
RSS_FEEDS = [
    "https://www.yoursolopreneur.com/feed/",
    "https://feeds.feedburner.com/SmallBusinessTrends",
    "https://www.entrepreneur.com/latest.rss",
]

# ── Perplexity API ──
PERPLEXITY_API_KEY = os.environ.get("PERPLEXITY_API_KEY", "")
PERPLEXITY_MODEL = "sonar"

# Targeted research queries for AI + small business content
PERPLEXITY_QUERIES = [
    "AI tools saving small businesses time and money this week",
    "women entrepreneurs using AI to grow their business 2026",
    "free AI tools for solopreneurs and small business owners",
    "AI automation replacing tasks for small business owners",
]

# ── Claude API ──
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = "claude-haiku-4-5-20251001"

# ── Content Mix Targets ──
CATEGORY_TARGETS = {
    "ai-news": 5,
    "how-to": 3,
    "thought-leadership": 2,
    "engagement": 2,
    "promo": 1,
}
TOTAL_ITEMS_MIN = 6
TOTAL_ITEMS_MAX = 8

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
DIGEST_DATA_DIR = os.path.join(BASE_DIR, "digest_data")
LATEST_DIGEST_FILE = os.path.join(DIGEST_DATA_DIR, "latest_digest.json")
LAST_THREAD_FILE = os.path.join(DIGEST_DATA_DIR, "last_thread_id.txt")
PROCESSED_REPLIES_FILE = os.path.join(DIGEST_DATA_DIR, "processed_replies.json")

# ── Google Drive ──
DRIVE_FOLDER_ID = os.environ.get("DRIVE_FOLDER_ID", "")
