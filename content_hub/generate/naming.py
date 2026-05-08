"""File/folder naming helpers.

Slugs are safe for Mac/Linux/Drive filenames: lowercase, ascii-ish, hyphens.
"""

import re
import unicodedata


def slugify(text: str, max_len: int = 60) -> str:
    if not text:
        return "untitled"
    # Strip accents (é → e) and keep ascii
    s = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    s = s.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_-]+", "-", s).strip("-")
    s = s[:max_len].rstrip("-")
    return s or "untitled"


def hook_line(draft_text: str) -> str:
    """First non-empty line of a draft — the hook/title."""
    for line in (draft_text or "").splitlines():
        line = line.strip()
        if line:
            return line
    return ""


def video_title_from_caption(caption: str) -> str:
    """YouTube fetcher stores caption as 'title\\n\\ndescription'. First line = title."""
    for line in (caption or "").splitlines():
        line = line.strip()
        if line:
            return line
    return ""


def ensure_unique(path_factory, base_slug: str) -> str:
    """Given a callable that takes a slug and returns a Path, append -2, -3…
    until the path doesn't exist. Used to keep two drafts with identical
    hooks from clobbering each other.
    """
    slug = base_slug
    i = 2
    while path_factory(slug).exists():
        slug = f"{base_slug}-{i}"
        i += 1
    return slug
