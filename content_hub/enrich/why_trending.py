"""One-sentence 'why this is trending' summary via Claude Haiku."""

import logging

import httpx

from ..config import ANTHROPIC_API_KEY, HAIKU_MODEL

log = logging.getLogger(__name__)

PROMPT = (
    "You label why a social-media post is working for a small-business AI coach audience. "
    "Reply with ONE sentence (max 18 words) naming the angle + what makes it click. "
    "No preamble, no quotes."
)


def why_trending(caption: str, channel: str, format_tag: str) -> str:
    if not ANTHROPIC_API_KEY or not caption:
        return ""
    try:
        with httpx.Client(timeout=30) as client:
            r = client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": HAIKU_MODEL,
                    "max_tokens": 60,
                    "system": PROMPT,
                    "messages": [{
                        "role": "user",
                        "content": f"Channel: {channel}\nFormat: {format_tag}\nPost:\n{caption[:1200]}",
                    }],
                },
            )
            r.raise_for_status()
            data = r.json()
            return data["content"][0]["text"].strip()
    except Exception as e:
        log.warning("why_trending failed: %s", e)
        return ""
