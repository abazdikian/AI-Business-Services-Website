"""YouTube fetcher — Apify actor: streamers/youtube-scraper."""

from .apify_client import retry_run, safe
from .base import Post, within_lookback
from ..config import APIFY_ACTORS, LOOKBACK_DAYS


def _to_post(item: dict, source: str = "creator") -> Post | None:
    vid = item.get("id") or item.get("videoId")
    if not vid:
        return None
    url = item.get("url") or f"https://www.youtube.com/watch?v={vid}"
    item_type = (item.get("type") or "").lower()
    media_type = "short" if item_type == "shorts" else "long-video"
    return Post(
        id=f"yt_{vid}",
        channel="youtube",
        creator_handle=item.get("channelUsername") or item.get("channelName"),
        post_url=url,
        thumbnail_url=item.get("thumbnailUrl") or safe(item, "thumbnails", "default", "url"),
        posted_at=item.get("date") or item.get("publishedAt"),
        caption=(item.get("title") or "") + ("\n\n" + item["text"] if item.get("text") else ""),
        likes=int(item.get("likes") or 0),
        comments=int(item.get("commentsCount") or item.get("comments") or 0),
        views=int(item.get("viewCount") or item.get("views") or 0),
        followers=int(item.get("numberOfSubscribers") or 0) or None,
        media_type=media_type,
        source=source,
        raw=item,
    )


def fetch_creators(urls: list[str], per_creator: int) -> list[Post]:
    if not urls:
        return []
    items = retry_run(APIFY_ACTORS["youtube"], {
        "startUrls": [{"url": u} for u in urls],
        "maxResults": per_creator,
        "maxResultsShorts": per_creator,
        "dateFilter": "week",
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
    items = retry_run(APIFY_ACTORS["youtube"], {
        "searchQueries": queries,
        "maxResults": per_query,
        "dateFilter": "week",
    })
    out: list[Post] = []
    for it in items:
        p = _to_post(it, source="hashtag")
        if p and within_lookback(p.posted_at, LOOKBACK_DAYS):
            out.append(p)
    return out
