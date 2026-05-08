"""
Configuration for the Reddit Scout Agent.
Hourly engagement scanner that finds reply opportunities in SMB subreddits.
"""

import os

# ── Subreddits to Monitor ──
SCOUT_SUBREDDITS = [
    {"name": "smallbusiness", "url": "https://www.reddit.com/r/smallbusiness/new.json?limit=25"},
    {"name": "Solopreneur", "url": "https://www.reddit.com/r/Solopreneur/new.json?limit=25"},
    {"name": "EntrepreneurRideAlong", "url": "https://www.reddit.com/r/EntrepreneurRideAlong/new.json?limit=25"},
    {"name": "startups", "url": "https://www.reddit.com/r/startups/new.json?limit=25"},
    {"name": "AiForSmallBusiness", "url": "https://www.reddit.com/r/AiForSmallBusiness/new.json?limit=25"},
    {"name": "Shopify", "url": "https://www.reddit.com/r/Shopify/new.json?limit=25"},
]

# ── Scoring Thresholds ──
HOT_THRESHOLD = 7         # Score >= 7 + fresh -> instant alert
WARM_THRESHOLD = 5         # Score >= 5 -> morning summary
MAX_POST_AGE_HOURS = 2     # Only HOT-alert on posts < 2h old
SEEN_POSTS_TTL_DAYS = 7    # Purge seen posts older than 7 days

# ── Active Hours (Eastern Time) ──
ACTIVE_HOURS_START = 7     # 7am ET
ACTIVE_HOURS_END = 22      # 10pm ET

# ── Fetch Settings ──
REDDIT_HEADERS = {"User-Agent": "SmallBizAICoach/2.0 (reddit-scout)"}
REDDIT_MIN_TITLE_LEN = 30  # Skip low-effort titles

# ── Keywords that boost scoring (context for Claude prompt) ──
OPPORTUNITY_KEYWORDS = [
    "AI automation", "automate", "AI tools", "ChatGPT for business",
    "Claude for business", "need help with AI", "AI consultant",
    "AI coach", "overwhelmed", "too many tools", "manual process",
    "AI training", "AI workshop", "implement AI", "AI strategy",
    "small business AI", "AI for my business", "automate my",
    "save time", "hiring VA", "virtual assistant", "workflow",
]

# ── Paths ──
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCOUT_DATA_DIR = os.path.join(BASE_DIR, "scout_data")
SEEN_POSTS_FILE = os.path.join(SCOUT_DATA_DIR, "seen_posts.json")
WARM_QUEUE_FILE = os.path.join(SCOUT_DATA_DIR, "warm_queue.json")
