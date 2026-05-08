"""LinkedIn fetcher — Apify actor: apimaestro/linkedin-profile-posts."""

from .apify_client import retry_run, safe
from .base import Post, within_lookback
from ..config import APIFY_ACTORS, LOOKBACK_DAYS


def _to_post(item: dict) -> Post | None:
    urn = safe(item, "full_urn") or safe(item, "urn", "activity_urn")
    if not urn:
        return None

    author = item.get("author") or {}
    stats = item.get("stats") or {}
    media = item.get("media") or {}
    posted = item.get("posted_at") or {}

    thumb = None
    media_subtype = None
    if isinstance(media, dict):
        media_subtype = (media.get("type") or "").lower()
        if media_subtype in ("image", "video"):
            thumb = media.get("url") or media.get("thumbnail")
    thumb = thumb or author.get("profile_picture")

    post_type = (item.get("post_type") or "").lower()
    if "article" in post_type:
        media_type = "article"
    elif "document" in post_type or "carousel" in post_type:
        media_type = "carousel"
    elif media_subtype == "video":
        media_type = "video"
    elif media_subtype == "image":
        media_type = "image"
    else:
        media_type = "text"

    return Post(
        id=f"li_{urn}",
        channel="linkedin",
        creator_handle=author.get("username"),
        post_url=item.get("url"),
        thumbnail_url=thumb,
        posted_at=posted.get("date") if isinstance(posted, dict) else posted,
        caption=item.get("text") or "",
        likes=int(stats.get("total_reactions") or 0),
        comments=int(stats.get("comments") or 0),
        shares=int(stats.get("reposts") or 0),
        views=0,
        followers=None,
        media_type=media_type,
        source="creator",
        raw=item,
    )


def fetch_creators(urls: list[str], per_creator: int) -> list[Post]:
    if not urls:
        return []
    out: list[Post] = []
    for u in urls:
        username = u.rstrip("/").split("/")[-1]
        items = retry_run(APIFY_ACTORS["linkedin"], {
            "username": username,
            "limit": per_creator,
        })
        for it in items:
            p = _to_post(it)
            if p and within_lookback(p.posted_at, LOOKBACK_DAYS):
                out.append(p)
    return out


def fetch_hashtags(queries: list[str], per_query: int) -> list[Post]:
    return []
