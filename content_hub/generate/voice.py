"""Load Alice's voice profile from voice_samples/alice_posts.md.

The markdown file is the source of truth: examples + the 'Voice register notes'
section at the bottom. We pass it to the drafter verbatim — the model gets both
the rules and the exemplars in one shot.
"""

from pathlib import Path

from ..config import BASE_DIR

VOICE_FILE = BASE_DIR / "voice_samples" / "alice_posts.md"


def load_voice_profile() -> str:
    if not VOICE_FILE.exists():
        return ""
    return VOICE_FILE.read_text(encoding="utf-8")
