"""Classify a post's format tag from fetcher media_type + channel."""

_MAP = {
    ("youtube", "short"): "short",
    ("youtube", "long-video"): "long-video",
    ("tiktok", "short"): "short",
    ("instagram", "reel"): "reel",
    ("instagram", "carousel"): "carousel",
    ("instagram", "static"): "static",
    ("linkedin", "carousel"): "carousel",
    ("linkedin", "text"): "text",
    ("linkedin", "article"): "article",
    ("facebook", "video"): "video",
    ("facebook", "static"): "static",
}


def format_tag_for(channel: str, media_type: str | None) -> str:
    if not media_type:
        return "static"
    return _MAP.get((channel, media_type), media_type)
