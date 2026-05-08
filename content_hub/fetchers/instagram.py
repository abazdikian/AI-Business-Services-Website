"""Instagram fetcher — Apify actor: apify/instagram-scraper."""

from .apify_client import retry_run
from .base import Post, within_lookback
from ..config import APIFY_ACTORS, LOOKBACK_DAYS


def _media_type(item: dict) -> str:
    t = (item.get("type") or item.get("productType") or "").lower()
    if "carousel" in t or "sidecar" in t:
        return "carousel"
    if "reel" in t or "video" in t or "clips" in t:
        return "reel"
    return "static"


def _to_post(item: dict, source: str) -> Post | None:
    pid = item.get("id") or item.get("shortCode") or item.get("url")
    if not pid:
        return None
    return Post(
        id=f"ig_{pid}",
        channel="instagram",
        creator_handle=item.get("ownerUsername") or item.get("ownerFullName"),
        post_url=item.get("url"),
        thumbnail_url=item.get("displayUrl") or item.get("thumbnailUrl"),
        posted_at=item.get("timestamp") or item.get("takenAtTimestamp"),
        caption=item.get("caption") or "",
        likes=int(item.get("likesCount") or 0),
        comments=int(item.get("commentsCount") or 0),
        views=int(item.get("videoViewCount") or item.get("videoPlayCount") or 0),
        followers=int(item.get("ownerFollowersCount") or 0) or None,
        media_type=_media_type(item),
        source=source,
        raw=item,
    )


def fetch_creators(urls: list[str], per_creator: int) -> list[Post]:
    if not urls:
        return []
    items = retry_run(APIFY_ACTORS["instagram"], {
        "directUrls": urls,
        "resultsLimit": per_creator,
        "resultsType": "posts",
        "searchLimit": 1,
        "addParentData": False,
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
    tag_urls = [f"https://www.instagram.com/explore/tags/{q.lstrip('#')}/" for q in queries]
    items = retry_run(APIFY_ACTORS["instagram"], {
        "directUrls": tag_urls,
        "resultsLimit": per_query,
        "resultsType": "posts",
        "searchLimit": 1,
        "addParentData": False,
    })
    out: list[Post] = []
    for it in items:
        p = _to_post(it, source="hashtag")
        if p and within_lookback(p.posted_at, LOOKBACK_DAYS):
            out.append(p)
    return out
