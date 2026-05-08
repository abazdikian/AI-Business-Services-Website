"""Normalized Post shape returned by every fetcher."""

from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class Post:
    id: str
    channel: str
    creator_handle: str | None = None
    post_url: str | None = None
    thumbnail_url: str | None = None
    posted_at: str | None = None
    caption: str = ""
    likes: int = 0
    comments: int = 0
    shares: int = 0
    views: int = 0
    followers: int | None = None
    media_type: str | None = None
    source: str = "creator"
    raw: dict = field(default_factory=dict)

    def to_row(self) -> dict[str, Any]:
        return asdict(self)


def within_lookback(posted_at_iso: str | None, days: int) -> bool:
    if not posted_at_iso:
        return True
    try:
        dt = datetime.fromisoformat(posted_at_iso.replace("Z", "+00:00"))
    except ValueError:
        return True
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    age_days = (datetime.now(timezone.utc) - dt).days
    return age_days <= days
