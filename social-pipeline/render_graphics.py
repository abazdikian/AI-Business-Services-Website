"""
Render branded HTML templates to PNG (single images) and PDF (carousels)
using Playwright headless Chromium.
"""

import os
import re
from playwright.sync_api import sync_playwright
from PIL import Image
from config import BASE_DIR, OUTPUT_DIR

TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

CATEGORY_LABELS = {
    "ai-news": "AI NEWS",
    "how-to": "HOW-TO",
    "thought-leadership": "HOT TAKE",
    "engagement": "ENGAGEMENT",
    "promo": "YOUR BUSINESS",
}


def _read_template(name):
    path = os.path.join(TEMPLATES_DIR, name)
    with open(path) as f:
        return f.read()


def _gold_accent(headline):
    """Wrap the last word in a gold span for visual emphasis."""
    words = headline.rstrip(".!?").split()
    if len(words) < 2:
        return headline
    last_word = words[-1]
    rest = " ".join(words[:-1])
    trailing = ""
    if headline[-1] in ".!?":
        trailing = headline[-1]
    return f'{rest} <span class="gold">{last_word}</span>{trailing}'


def _bullets_html(caption):
    """Extract arrow bullet lines from caption and wrap in <li> tags."""
    lines = caption.split("\n")
    bullets = []
    for line in lines:
        line = line.strip()
        if line.startswith("→"):
            text = line.lstrip("→").strip()
            bullets.append(f'<li><span class="arrow">→</span>{text}</li>')
    if not bullets:
        for line in lines:
            line = line.strip()
            if line and not line.startswith("#") and len(line) > 10:
                bullets.append(f'<li><span class="arrow">→</span>{line}</li>')
                if len(bullets) >= 3:
                    break
    return "\n    ".join(bullets)


def render_quote_hook(item, output_path):
    """Render a Quote/Hook single image (1080x1080) as PNG."""
    html = _read_template("quote_hook.html")
    cat = item.get("category", "thought-leadership")

    html = html.replace("{{CATEGORY_LEFT}}", CATEGORY_LABELS.get(cat, "INSIGHT"))
    html = html.replace("{{CATEGORY_RIGHT}}", "QUOTES" if cat == "engagement" else CATEGORY_LABELS.get(cat, ""))
    html = html.replace("{{HEADLINE}}", _gold_accent(item.get("headline", "")))

    return _render_png(html, output_path, 1080, 1080)


def render_text_announcement(item, output_path):
    """Render a Text/Announcement single image (1080x1080) as PNG."""
    html = _read_template("text_announcement.html")
    cat = item.get("category", "ai-news")
    caption = item.get("caption", "")
    summary = item.get("summary", "")
    body = summary.split(". ")[0] + "." if ". " in summary else summary

    html = html.replace("{{CATEGORY}}", CATEGORY_LABELS.get(cat, "AI NEWS"))
    html = html.replace("{{HEADLINE}}", item.get("headline", ""))
    html = html.replace("{{BODY}}", body)
    html = html.replace("{{BULLETS}}", _bullets_html(caption))

    return _render_png(html, output_path, 1080, 1080)


def render_carousel(item, output_dir):
    """Render a full carousel (cover + content slides + CTA) as PDF."""
    cat = item.get("category", "ai-news")
    carousel_points = item.get("carousel_points", [])

    if not carousel_points:
        print(f"  [WARN] No carousel_points for '{item.get('headline', '')}' — skipping carousel")
        return None

    slide_paths = []

    # Cover slide
    html = _read_template("carousel_cover.html")
    html = html.replace("{{CATEGORY}}", CATEGORY_LABELS.get(cat, "AI FOR BUSINESS"))
    html = html.replace("{{HEADLINE}}", item.get("headline", ""))
    html = html.replace("{{SUBTITLE}}", item.get("summary", "")[:120])
    html = html.replace("{{TEASER}}", f"{len(carousel_points)} key insights inside →")
    cover_path = os.path.join(output_dir, "slide-00-cover.png")
    _render_png(html, cover_path, 1080, 1350)
    slide_paths.append(cover_path)

    # Content slides
    for i, point in enumerate(carousel_points):
        html = _read_template("carousel_content.html")
        html = html.replace("{{NUMBER}}", point.get("number", f"{i+1:02d}"))
        html = html.replace("{{TITLE}}", point.get("title", ""))
        html = html.replace("{{BODY}}", point.get("body", "").replace("\n", "<br>"))
        slide_path = os.path.join(output_dir, f"slide-{i+1:02d}-content.png")
        _render_png(html, slide_path, 1080, 1350)
        slide_paths.append(slide_path)

    # CTA slide (static — no placeholders)
    cta_html = _read_template("carousel_cta.html")
    cta_path = os.path.join(output_dir, "slide-99-cta.png")
    _render_png(cta_html, cta_path, 1080, 1350)
    slide_paths.append(cta_path)

    # Combine into PDF
    pdf_path = os.path.join(output_dir, "linkedin-carousel.pdf")
    _combine_pngs_to_pdf(slide_paths, pdf_path)

    return pdf_path


def _render_png(html_content, output_path, width, height):
    """Render HTML string to PNG using Playwright."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": height})
        page.set_content(html_content, wait_until="networkidle")
        page.wait_for_timeout(1500)
        page.screenshot(path=output_path, full_page=False)
        browser.close()

    print(f"  [Render] {os.path.basename(output_path)} ({width}x{height})")
    return output_path


def _combine_pngs_to_pdf(png_paths, pdf_path):
    """Combine multiple PNG slide images into a single PDF."""
    images = []
    for path in png_paths:
        img = Image.open(path).convert("RGB")
        images.append(img)

    if images:
        images[0].save(pdf_path, save_all=True, append_images=images[1:], resolution=150)
        print(f"  [PDF] {os.path.basename(pdf_path)} ({len(images)} pages)")

    return pdf_path


def render_post(item, output_dir):
    """Render all graphics for a single post item."""
    os.makedirs(output_dir, exist_ok=True)
    cat = item.get("category", "ai-news")

    # Single image (PNG)
    png_path = os.path.join(output_dir, "instagram-1080x1080.png")
    if cat in ("thought-leadership", "engagement"):
        render_quote_hook(item, png_path)
    else:
        render_text_announcement(item, png_path)

    # Carousel (PDF) — skip for engagement posts
    pdf_path = None
    if cat != "engagement":
        pdf_path = render_carousel(item, output_dir)

    return {"png": png_path, "pdf": pdf_path}


if __name__ == "__main__":
    sample = {
        "headline": "I Fired My VA. Here's What Replaced Her.",
        "summary": "One solopreneur replaced $4K/month in admin help with 3 free AI tools.",
        "caption": "Your AI just became your executive assistant.\n\n→ Claude for email drafts + proposals\n→ Notion AI for meeting notes\n→ Calendly + Zapier for auto-scheduling\n\nThis changes everything for solopreneurs.",
        "category": "how-to",
        "carousel_points": [
            {"number": "01", "title": "Claude for Email + Proposals", "body": "Draft client emails in 30 seconds. Generate proposals from a brief. Review contracts before you sign."},
            {"number": "02", "title": "Notion AI for Meeting Notes", "body": "Record, transcribe, and summarize every meeting automatically. Never miss an action item again."},
            {"number": "03", "title": "Calendly + Zapier for Scheduling", "body": "Clients book themselves. Confirmation emails go out. Your calendar stays clean. Zero manual work."},
        ],
    }

    test_dir = os.path.join(OUTPUT_DIR, "test-render")
    result = render_post(sample, test_dir)
    print(f"\nPNG: {result['png']}")
    print(f"PDF: {result['pdf']}")
