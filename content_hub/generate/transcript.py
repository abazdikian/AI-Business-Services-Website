"""YouTube transcript fetcher.

Uses youtube-transcript-api (free, no keys). Returns plain-text transcript +
optional time-coded chunks for speaker notes. Returns None if the video has
no captions (common for music videos, live streams, etc.).
"""

import logging
import re
from typing import Any

log = logging.getLogger(__name__)

_YT_ID_PATTERNS = [
    re.compile(r"(?:youtube\.com/watch\?v=)([A-Za-z0-9_-]{11})"),
    re.compile(r"(?:youtu\.be/)([A-Za-z0-9_-]{11})"),
    re.compile(r"(?:youtube\.com/shorts/)([A-Za-z0-9_-]{11})"),
    re.compile(r"(?:youtube\.com/embed/)([A-Za-z0-9_-]{11})"),
]


def extract_video_id(url_or_id: str) -> str | None:
    if not url_or_id:
        return None
    s = url_or_id.strip()
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", s):
        return s
    for pat in _YT_ID_PATTERNS:
        m = pat.search(s)
        if m:
            return m.group(1)
    return None


def fetch_transcript(url_or_id: str) -> dict[str, Any] | None:
    """Return {text, chunks, language} or None if unavailable."""
    vid = extract_video_id(url_or_id)
    if not vid:
        log.warning("no video id parsed from %r", url_or_id)
        return None

    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        from youtube_transcript_api._errors import (
            TranscriptsDisabled, NoTranscriptFound, VideoUnavailable,
        )
    except ImportError as e:
        log.error("youtube-transcript-api not installed: %s", e)
        return None

    try:
        api = YouTubeTranscriptApi()
        fetched = api.fetch(vid, languages=["en", "en-US", "en-GB"])
    except (TranscriptsDisabled, NoTranscriptFound, VideoUnavailable) as e:
        log.warning("no transcript for %s: %s", vid, type(e).__name__)
        return None
    except Exception as e:
        log.warning("transcript fetch failed for %s: %s", vid, e)
        return None

    chunks = [
        {"start": float(s.start), "duration": float(s.duration), "text": s.text}
        for s in fetched
    ]
    text = " ".join(c["text"] for c in chunks).strip()
    return {
        "video_id": vid,
        "language": getattr(fetched, "language_code", "en"),
        "text": text,
        "chunks": chunks,
    }


def format_timestamp(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h:d}:{m:02d}:{s:02d}" if h else f"{m:d}:{s:02d}"
