"""TikTok fetcher — Apify actor: clockworks/tiktok-scraper."""

from .apify_client import retry_run
from .base import Post, within_lookback
from ..config import APIFY_ACTORS, LOOKBACK_DAYS


def _to_post(item: dict, source: str) -> Post | None:
    vid = item.get("id") or item.get("webVideoUrl")
    if not vid:
        return None
    return Post(
        id=f"tt_{vid}",
        channel="tiktok",
        creator_handle=(item.get("authorMeta") or {}).get("name") or item.get("authorName"),
        post_url=item.get("webVideoUrl"),
        thumbnail_url=(item.get("videoMeta") or {}).get("coverUrl") or item.get("covers", {}).get("default"),
        posted_at=item.get("createTimeISO") or item.get("createTime"),
        caption=item.get("text") or "",
        likes=int(item.get("diggCount") or 0),
        comments=int(item.get("commentCount") or 0),
        shares=int(item.get("shareCount") or 0),
        views=int(item.get("playCount") or 0),
        followers=int((item.get("authorMeta") or {}).get("fans") or 0) or None,
        media_type="short",
        source=source,
        raw=item,
    )


def fetch_creators(urls: list[str], per_creator: int) -> list[Post]:
    if not urls:
        return []
    items = retry_run(APIFY_ACTORS["tiktok"], {
        "profiles": [u.rstrip("/").split("@")[-1] for u in urls],
        "resultsPerPage": per_creator,
        "shouldDownloadVideos": False,
    })
    out: list[Post] = []
    for it in items:
        p = _to_post(it, source="creator")
        if p and within_lookback(p.posted_at, LOOKBACK_DAYS):
            out.append(p)
    return out


def fetch_hashtags(queries: list[str], per_query: int) -> list[Post]:
    if not queries:
        return []
    items = retry_run(APIFY_ACTORS["tiktok"], {
        "hashtags": queries,
        "resultsPerPage": per_query,
        "shouldDownloadVideos": False,
    })
    out: list[Post] = []
    for it in items:
        p = _to_post(it, source="hashtag")
        if p and within_lookback(p.posted_at, LOOKBACK_DAYS):
            out.append(p)
    return out
