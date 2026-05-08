"""Branded LinkedIn infographic — white background, burgundy lines, black text.

Portrait 1080×1350. Reusable across weekly topics — feed it a data dict
matching INFOGRAPHIC_SCHEMA and you get a consistent branded PNG + PDF.

Template file: content_hub/render/templates/infographic.html
Logo is inlined as a base64 data URI from templates/_logo_data_uri.txt so
the render is self-contained (no external font/image fetches except Google
Fonts for Archivo Black + Inter).

Render:
    from content_hub.render.infographic import render_infographic
    render_infographic(my_data, out_dir=Path("drafts/..."), slug="my-topic")

Data schema (INFOGRAPHIC_SCHEMA):
    {
        "title":            str   # big Archivo Black headline (~28-32 chars max reads best)
        "subtitle":         str   # one-line subtitle under the burgundy bar
        "badge_text_top":   str   # top line of the pill badge top-right (e.g. "10")
        "badge_text_bottom":str   # bottom line of the pill (e.g. "ESSENTIAL")
        "section_1_label":  str   # first section header (e.g. "Foundations")
        "section_1_count":  str   # count label (e.g. "5")
        "section_1":        [     # EXACTLY 5 cards — layout is a 5-col row
            {"name": str, "icon": str (emoji), "desc": str}  # benefit in <10 words
        ]
        "section_2_label":  str
        "section_2_count":  str
        "section_2":        [     # same shape — EXACTLY 5 cards
            {"name": str, "icon": str, "desc": str}
        ]
        "github_link":      str   # e.g. "github.com/x/y" (bottom strip)
        "week_label":       str   # footer left text, e.g. "Week of April 13 · 2026"
        "logo_uri":         str   # optional — falls back to _LOGO_URI constant
    }

To create a new infographic, copy one of the preset dicts below
(`TOP_CLAUDE_CODE_SKILLS`) and change the values. Keep the schema the same
so every weekly infographic shares the same layout and visual weight.
"""

from __future__ import annotations

import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from playwright.sync_api import sync_playwright

from .pdf import build_carousel_pdf

log = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).parent / "templates"
_env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=select_autoescape(["html"]),
)
_LOGO_URI = (TEMPLATES_DIR / "_logo_data_uri.txt").read_text().strip()


def render_infographic(data: dict, out_dir: Path, *, slug: str = "infographic") -> dict:
    """Render the infographic to PNG + PDF. Returns {png, pdf} paths.

    `data` must match INFOGRAPHIC_SCHEMA (see module docstring). If
    `logo_uri` is not set in the data dict, the bundled brand logo is used.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    data = dict(data)  # don't mutate caller's dict
    data.setdefault("logo_uri", _LOGO_URI)
    tpl = _env.get_template("infographic.html")
    html = tpl.render(**data)
    png_path = out_dir / f"{slug}.png"
    pdf_path = out_dir / f"{slug}.pdf"

    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(
            viewport={"width": 1080, "height": 1350},
            device_scale_factor=1,
        )
        try:
            page = context.new_page()
            page.set_default_timeout(60000)
            page.set_content(html, wait_until="load", timeout=60000)
            try:
                page.evaluate("document.fonts.ready")
            except Exception:
                pass
            page.wait_for_timeout(600)
            page.screenshot(path=str(png_path), full_page=False, type="png")
            log.info("rendered %s", png_path.name)
        finally:
            context.close()
            browser.close()

    build_carousel_pdf([png_path], pdf_path)
    return {"png": png_path, "pdf": pdf_path}


# ──────────────────────────────────────────────────────────────────────
# Preset content — copy and modify for new weekly infographics
# ──────────────────────────────────────────────────────────────────────

TOP_CLAUDE_CODE_SKILLS: dict = {
    "title": "Top Claude Code Skills",
    "subtitle": "you can't NOT use in your business workflow",
    "badge_text_top": "10",
    "badge_text_bottom": "ESSENTIAL",
    "section_1_label": "Foundations",
    "section_1_count": "5",
    "section_1": [
        {"name": "Skills", "icon": "🧩",
         "desc": "install expert capabilities in one click"},
        {"name": "MCP", "icon": "🔌",
         "desc": "kill the copy-paste tax forever"},
        {"name": "Hooks", "icon": "⚙️",
         "desc": "workflows run while you sleep"},
        {"name": "Memory", "icon": "🧠",
         "desc": "stop re-explaining yourself each session"},
        {"name": "Plans", "icon": "🗺️",
         "desc": "cut rework in half — plan before build"},
    ],
    "section_2_label": "Power Moves",
    "section_2_count": "5",
    "section_2": [
        {"name": "Frontend Design", "icon": "🎨",
         "desc": "pro-looking UI without hiring a designer"},
        {"name": "Playwright", "icon": "🎭",
         "desc": "the web works for you, hands-free"},
        {"name": "Subagents", "icon": "👥",
         "desc": "10 things done at once — finish by noon"},
        {"name": "/compact", "icon": "📦",
         "desc": "long chats stay sharp, never lose context"},
        {"name": "Worktrees", "icon": "🌳",
         "desc": "build 3 versions at once, pick the winner"},
    ],
    "github_link": "github.com/hesreallyhim/awesome-claude-code",
    "week_label": "Week of April 13 · 2026",
}

# Back-compat alias
TOP_CLAUDE_SKILLS_DEFAULT = TOP_CLAUDE_CODE_SKILLS

# ──────────────────────────────────────────────────────────────────────
# Starter stub — copy this block, fill in your content, call
#   render_infographic(MY_PRESET, Path("/path/to/out"), slug="my-topic")
# ──────────────────────────────────────────────────────────────────────

EMPTY_PRESET: dict = {
    "title": "TOPIC TITLE",
    "subtitle": "one-line subtitle",
    "badge_text_top": "10",
    "badge_text_bottom": "ESSENTIAL",
    "section_1_label": "Section 1",
    "section_1_count": "5",
    "section_1": [
        {"name": "NAME", "icon": "🔸", "desc": "short benefit"},
        {"name": "NAME", "icon": "🔸", "desc": "short benefit"},
        {"name": "NAME", "icon": "🔸", "desc": "short benefit"},
        {"name": "NAME", "icon": "🔸", "desc": "short benefit"},
        {"name": "NAME", "icon": "🔸", "desc": "short benefit"},
    ],
    "section_2_label": "Section 2",
    "section_2_count": "5",
    "section_2": [
        {"name": "NAME", "icon": "🔸", "desc": "short benefit"},
        {"name": "NAME", "icon": "🔸", "desc": "short benefit"},
        {"name": "NAME", "icon": "🔸", "desc": "short benefit"},
        {"name": "NAME", "icon": "🔸", "desc": "short benefit"},
        {"name": "NAME", "icon": "🔸", "desc": "short benefit"},
    ],
    "github_link": "github.com/…",
    "week_label": "Week of …",
}
