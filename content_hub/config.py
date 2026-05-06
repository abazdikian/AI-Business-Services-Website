"""Configuration for the Content Hub dashboard."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
DB_PATH = BASE_DIR / "hub.db"
FIXTURES_DIR = BASE_DIR / "fixtures"


def _load_dotenv() -> None:
    for p in (PROJECT_ROOT / ".env", BASE_DIR / ".env"):
        if not p.exists():
            continue
        for line in p.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_load_dotenv()

APIFY_TOKEN = os.environ.get("APIFY_TOKEN") or os.environ.get("APIFY_API_TOKEN", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
HAIKU_MODEL = "claude-haiku-4-5-20251001"

ALICE_EMAIL = "abazdikian@gmail.com"
DRIVE_FOLDER_ID = os.environ.get("DRIVE_FOLDER_ID", "")
DRIVE_ROOT_NAME = "content-hub-drafts"

BRAND = {
    "burgundy": "#7A1F2B",
    "gold": "#C9A24B",
    "eggshell": "#F7F3EE",
    "ink": "#1F1A17",
    "muted": "#7A6E63",
}

CHANNELS = ["youtube", "linkedin", "tiktok", "instagram"]

CREATORS = {
    "youtube": [
        "https://www.youtube.com/@sabrina_ramonov",
        "https://www.youtube.com/@nateherk",
        "https://www.youtube.com/@GregIsenberg",
        "https://www.youtube.com/@duncanrogoff",
        "https://www.youtube.com/@mavgpt",
    ],
    "linkedin": [
        "https://www.linkedin.com/in/monikamileva1/",
        "https://www.linkedin.com/in/awa-k-penn/",
        "https://www.linkedin.com/in/sabrinaramonov/",
        "https://www.linkedin.com/in/nateherkelman/",
    ],
    "tiktok": [
        "https://www.tiktok.com/@sabrina_ramonov",
        "https://www.tiktok.com/@brooke_wrightmode",
        "https://www.tiktok.com/@kristagreener",
        "https://www.tiktok.com/@taki.gpt",
        "https://www.tiktok.com/@iamkylebalmer",
        "https://www.tiktok.com/@pro.glitch",
        "https://www.tiktok.com/@wavaai.feeds",
        "https://www.tiktok.com/@robtheaiguy",
        "https://www.tiktok.com/@carter.braydon",
        "https://www.tiktok.com/@mavgpt",
    ],
    "instagram": [
        "https://www.instagram.com/zeeeljain/",
        "https://www.instagram.com/claudeai/",
        "https://www.instagram.com/adamstewartmarketing/",
        "https://www.instagram.com/chase.h.ai/",
        "https://www.instagram.com/wright_mode/",
        "https://www.instagram.com/nathanhodgson.ai/",
        "https://www.instagram.com/realrileybrown/",
        "https://www.instagram.com/khris.sheer/",
        "https://www.instagram.com/nateherkai/",
        "https://www.instagram.com/sabrina_ramonov/",
        "https://www.instagram.com/mavgpt/",
    ],
}

HASHTAGS = {
    "youtube": ["AI small business", "Claude automation"],
    "linkedin": ["AIforBusiness", "SmallBusinessAI"],
    "tiktok": ["AIforBusiness", "SmallBusinessAI", "ClaudeAI"],
    "instagram": ["AIforBusiness", "SmallBusinessAI", "ClaudeAI"],
}

CREATOR_POSTS_PER_CHANNEL = 5
HASHTAG_POSTS_PER_CHANNEL = 5
CREATOR_POSTS_OVERRIDE = {"instagram": 3}
LOOKBACK_DAYS = 7

APIFY_ACTORS = {
    "youtube": "streamers/youtube-scraper",
    "linkedin": "apimaestro/linkedin-profile-posts",
    "tiktok": "clockworks/tiktok-scraper",
    "instagram": "apify/instagram-scraper",
}
