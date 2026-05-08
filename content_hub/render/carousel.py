"""Render a carousel of slides to PNG via Playwright + Chromium.

All channels now render at 9:16 (1080×1920) to match Brand Refresh v2.

Cover alternates white/burgundy per post (hash on slug) so the profile grid
checkerboards automatically. Middle slides keep alternating; final slide is
always burgundy (CTA).
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from playwright.sync_api import sync_playwright

log = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).parent / "templates"
_env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=select_autoescape(["html"]),
)
SIZES: dict[str, tuple[int, int]] = {
    "4:5":  (1080, 1350),
    "9:16": (1080, 1920),
}

CHANNEL_SIZE: dict[str, str] = {
    "linkedin":  "4:5",   # LinkedIn document-carousel feed size (1080×1350)
    "instagram": "4:5",   # IG feed carousel size (1080×1350)
    "tiktok":    "9:16",  # TikTok / IG reel portrait (1080×1920)
}


def _title_size_class(title: str) -> str:
    """Pick a font-size class based on title length so long titles don't overflow."""
    n = len(title)
    if n <= 12:
        return "size-xl"
    if n <= 22:
        return "size-lg"
    if n <= 34:
        return "size-md"
    if n <= 48:
        return "size-sm"
    return "size-xs"


def _body_size_class(body: str) -> str:
    """Pick a font-size class based on the longest line and longest token."""
    text = (body or "").strip()
    lines = [l for l in text.split("\n") if l.strip()]
    longest_line = max((len(l) for l in lines), default=0) if lines else len(text)
    longest_token = max((len(t) for t in text.split()), default=0)
    if longest_token >= 22:
        return "size-xs"
    if longest_token >= 18:
        return "size-sm"
    if longest_line <= 40:
        return ""
    if longest_line <= 70:
        return "size-md"
    if longest_line <= 110:
        return "size-sm"
    return "size-xs"


def _cover_is_burgundy(cover_seed: str | None) -> bool:
    """Deterministic half/half split across posts by hashing the slug."""
    if cover_seed is None:
        return True
    h = hashlib.sha256(cover_seed.encode()).digest()[0]
    return (h % 2) == 0


def _bg_for(i: int, total: int, cover_burgundy: bool) -> str:
    """Alternate burgundy/white across slides. Odd-indexed slides match the
    cover color; even-indexed are the opposite. Guarantees no two same-color
    slides in a row and matches the Brand Refresh v2 carousel (Version A:
    white cover + white CTA; Version B: burgundy cover + burgundy CTA).
    """
    odd = (i % 2 == 1)
    matches_cover = odd
    if cover_burgundy:
        return "bg-burgundy" if matches_cover else "bg-white"
    return "bg-white" if matches_cover else "bg-burgundy"


def _eyebrow_for(i: int, total: int) -> str:
    if i == 1:
        return "THE PLAYBOOK"  # cover eyebrow — refresh voice
    if i == total:
        return "YOUR MOVE"
    return f"PART {i - 1:02d}"


def _page_label(i: int, total: int) -> str:
    return f"{i:02d} / {total:02d}"


def render_carousel(
    slides: list[dict],
    out_dir: Path,
    *,
    aspect: str = "9:16",
    filename_prefix: str = "slide",
    cover_seed: str | None = None,
    body_size_boost: bool = False,
    template: str = "default",
) -> list[Path]:
    """Render each slide to a PNG. Returns list of output paths in order.

    cover_seed: a stable string (e.g. the post slug). Drives whether the cover
    slide is burgundy or white so posts alternate on the profile grid.

    template: "default" uses slide.html (burgundy/white alternating). "editorial"
    uses slide_editorial.html (white pages, near-black ink, single gold rule;
    CTA slide reverts to standard burgundy gradient for visual punch).
    """
    if aspect not in SIZES:
        raise ValueError(f"unknown aspect {aspect!r}; use one of {list(SIZES)}")
    out_dir.mkdir(parents=True, exist_ok=True)
    width, height = SIZES[aspect]
    tall = aspect == "9:16"
    tpl_name = "slide_editorial.html" if template == "editorial" else "slide.html"
    tpl = _env.get_template(tpl_name)
    total = len(slides)
    cover_burgundy = _cover_is_burgundy(cover_seed)
    editorial = (template == "editorial")
    outputs: list[Path] = []

    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(
            viewport={"width": width, "height": height},
            device_scale_factor=1,
        )
        try:
            page = context.new_page()
            for i, s in enumerate(slides, 1):
                title = (s.get("title") or "").strip()
                body = (s.get("body") or s.get("sub_line") or "").strip()
                is_cta = (i == total and total > 1)
                if editorial:
                    bg_class = "bg-burgundy" if is_cta else "bg-white"
                else:
                    bg_class = _bg_for(i, total, cover_burgundy)
                eyebrow = s.get("eyebrow") or _eyebrow_for(i, total)
                html = tpl.render(
                    title=title,
                    body=body,
                    index=i,
                    total=total,
                    bg_class=bg_class,
                    eyebrow=eyebrow,
                    page_label=_page_label(i, total),
                    title_size_class=_title_size_class(title),
                    body_size_class=_body_size_class(body),
                    body_large=body_size_boost,
                    tall=tall,
                    is_cta=is_cta,
                    is_cover=(i == 1),
                )
                page.set_content(html, wait_until="load", timeout=60000)
                try:
                    page.evaluate("document.fonts.ready")
                except Exception:
                    pass
                page.wait_for_timeout(500)  # webfonts settle
                path = out_dir / f"{filename_prefix}-{i:02d}.png"
                page.screenshot(path=str(path), full_page=False, type="png",
                                omit_background=False)
                outputs.append(path)
                log.info("rendered %s (%dx%d)", path.name, width, height)
        finally:
            context.close()
            browser.close()
    return outputs
