"""
Batch-render LinkedIn carousel PDFs for the 2026-05-04 pillars.

Reads post.md files from content_hub/drafts/2026-05-04/linkedin/<slug>/post.md,
parses on `## Slide N — Title` separators, renders 4:5 PNGs, builds a PDF.

Local-only. No Drive upload (run upload separately once folder ID is confirmed).

Usage:
    content_hub/venv/bin/python scripts/render_linkedin_batch_2026_05_04.py
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from content_hub.render.carousel import render_carousel
from content_hub.render.pdf import build_carousel_pdf

WEEK = "2026-05-04"
DRAFTS = ROOT / "content_hub" / "drafts" / WEEK / "linkedin"
OUT_BASE = ROOT / "content_hub" / "output" / "linkedin"

# Render every pillar that has a post.md but no carousel.pdf yet.
SLUGS = [
    "messy-sops-to-10-hours-saved",
    "easiest-ai-stack-for-small-business",
    "5-monday-ai-questions-for-small-business",
    "ai-questions-when-creating-an-offer",
    "7-prompts-to-plan-a-marketing-month",
    "ai-as-your-invoice-assistant",
]

SLIDE_HEADER_RE = re.compile(r"^## Slide \d+ — (.+)$", re.MULTILINE)


def parse_slides(post_md: str) -> list[dict]:
    parts = SLIDE_HEADER_RE.split(post_md)
    # parts = [preamble, title1, body1, title2, body2, ...]
    slides = []
    for i in range(1, len(parts), 2):
        title = parts[i].strip()
        body = parts[i + 1].strip() if i + 1 < len(parts) else ""
        slides.append({"title": title, "body": body})
    return slides


def render_one(slug: str) -> Path | None:
    post_path = DRAFTS / slug / "post.md"
    if not post_path.exists():
        print(f"  SKIP {slug}: no post.md")
        return None

    slides = parse_slides(post_path.read_text(encoding="utf-8"))
    if len(slides) < 3:
        print(f"  FAIL {slug}: only {len(slides)} slides parsed")
        return None

    out_dir = OUT_BASE / slug
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"  → {slug} ({len(slides)} slides)")
    pngs = render_carousel(
        slides,
        out_dir,
        aspect="4:5",
        filename_prefix="slide",
        cover_seed=slug,
    )
    pdf_path = out_dir / "carousel.pdf"
    build_carousel_pdf(pngs, pdf_path)
    size_kb = pdf_path.stat().st_size // 1024
    print(f"    PDF: {pdf_path.relative_to(ROOT)} ({size_kb:,} KB)")

    # Also copy back into the drafts folder so review surfaces match
    drafts_pdf = DRAFTS / slug / "carousel.pdf"
    drafts_pdf.write_bytes(pdf_path.read_bytes())
    for p in pngs:
        (DRAFTS / slug / p.name).write_bytes(p.read_bytes())

    return pdf_path


def main():
    print(f"Rendering {len(SLUGS)} LinkedIn carousels for week {WEEK}\n")
    rendered = []
    for slug in SLUGS:
        pdf = render_one(slug)
        if pdf:
            rendered.append((slug, pdf))
    print(f"\nDone. Rendered {len(rendered)} of {len(SLUGS)} pillars.")
    for slug, pdf in rendered:
        print(f"  {slug}: {pdf.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
