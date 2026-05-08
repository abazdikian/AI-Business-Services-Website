# Social Media Template System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an automated graphic generation system that renders branded PNG images and PDF carousels from approved post drafts, triggered by email reply, uploaded to Google Drive.

**Architecture:** HTML/CSS templates in `social-pipeline/templates/` rendered via Playwright to PNG/PDF. Reply detection via Gmail API polling. Google Drive API for upload. Orchestrator ties reply → render → upload → confirmation email.

**Tech Stack:** Python 3, Playwright (headless Chromium), Google Drive API, Gmail API (existing auth), HTML/CSS templates with Google Fonts.

**Spec:** `docs/superpowers/specs/2026-04-05-template-system-design.md`

---

## File Structure

```
social-pipeline/
├── templates/
│   ├── quote_hook.html          # Quote/Hook single image (1080x1080)
│   ├── text_announcement.html   # Text/Announcement single image (1080x1080)
│   ├── carousel_cover.html      # Carousel cover slide (1080x1350)
│   ├── carousel_content.html    # Carousel content slide (1080x1350)
│   └── carousel_cta.html        # Carousel CTA slide (1080x1350)
├── render_graphics.py           # Playwright renders HTML → PNG/PDF
├── upload_drive.py              # Google Drive API upload
├── monitor_reply.py             # Gmail API polls for digest reply
├── generate_from_reply.py       # Orchestrator: parse reply → render → upload → confirm
├── digest_data/                 # Created at runtime
│   ├── latest_digest.json       # Saved drafted items from last pipeline run
│   ├── last_thread_id.txt       # Thread ID of last digest email
│   └── processed_replies.json   # Already-processed reply message IDs
├── config.py                    # Modified: add Drive folder ID, template paths
├── draft_posts.py               # Modified: add carousel_points to output
├── run_pipeline.py              # Modified: save digest data + thread ID
├── gmail_auth.py                # Modified: add Drive scope
└── requirements.txt             # Modified: add playwright
```

---

### Task 1: Create HTML templates

**Files:**
- Create: `social-pipeline/templates/quote_hook.html`
- Create: `social-pipeline/templates/text_announcement.html`
- Create: `social-pipeline/templates/carousel_cover.html`
- Create: `social-pipeline/templates/carousel_content.html`
- Create: `social-pipeline/templates/carousel_cta.html`

- [ ] **Step 1: Create the templates directory**

```bash
mkdir -p "/Users/alicebazidian/Desktop/AI Project/AI Services Website/social-pipeline/templates"
```

- [ ] **Step 2: Create quote_hook.html (1080x1080)**

The template uses `{{VARIABLE}}` placeholders that get replaced by Python's `str.replace()`.

```html
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;0,900;1,700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { width: 1080px; height: 1080px; overflow: hidden; }
  .slide {
    width: 1080px; height: 1080px;
    background: #7D2240; position: relative;
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    padding: 80px 90px; text-align: center;
  }
  .category-left {
    position: absolute; top: 48px; left: 56px;
    font-family: 'Inter', sans-serif; font-size: 16px; font-weight: 600;
    letter-spacing: 0.12em; text-transform: uppercase;
    color: rgba(247,243,238,0.45);
  }
  .category-right {
    position: absolute; top: 48px; right: 56px;
    font-family: 'Inter', sans-serif; font-size: 16px; font-weight: 600;
    letter-spacing: 0.12em; text-transform: uppercase;
    color: rgba(247,243,238,0.45);
  }
  .headline {
    font-family: 'Playfair Display', serif;
    font-size: 72px; font-weight: 900;
    color: #F7F3EE; line-height: 1.15;
    letter-spacing: -0.02em;
  }
  .headline .gold { color: #C9A847; font-style: italic; }
  .handle {
    position: absolute; bottom: 52px; left: 50%; transform: translateX(-50%);
    font-family: 'Inter', sans-serif; font-size: 18px; font-weight: 500;
    color: rgba(247,243,238,0.5);
    border: 1px solid rgba(247,243,238,0.2);
    padding: 8px 24px; border-radius: 100px;
  }
  .logo {
    position: absolute; bottom: 48px; right: 56px;
    font-family: 'Playfair Display', serif; font-size: 28px;
    font-weight: 700; color: #C9A847;
  }
</style>
</head>
<body>
<div class="slide">
  <span class="category-left">{{CATEGORY_LEFT}}</span>
  <span class="category-right">{{CATEGORY_RIGHT}}</span>
  <h1 class="headline">{{HEADLINE}}</h1>
  <span class="handle">@alicebazdikian</span>
  <span class="logo">AB</span>
</div>
</body>
</html>
```

- [ ] **Step 3: Create text_announcement.html (1080x1080)**

```html
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;0,900;1,700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { width: 1080px; height: 1080px; overflow: hidden; }
  .slide {
    width: 1080px; height: 1080px;
    background: #7D2240; position: relative;
    display: flex; flex-direction: column;
    justify-content: center;
    padding: 80px 80px 100px;
  }
  .eyebrow {
    font-family: 'Inter', sans-serif; font-size: 16px; font-weight: 600;
    letter-spacing: 0.14em; text-transform: uppercase;
    color: #C9A847; margin-bottom: 24px;
    display: flex; align-items: center; gap: 10px;
  }
  .eyebrow::before {
    content: ''; width: 28px; height: 2px; background: #C9A847;
  }
  .headline {
    font-family: 'Playfair Display', serif;
    font-size: 64px; font-weight: 900;
    color: #F7F3EE; line-height: 1.12;
    letter-spacing: -0.02em; margin-bottom: 28px;
  }
  .body-text {
    font-family: 'Inter', sans-serif; font-size: 24px;
    color: rgba(247,243,238,0.75); line-height: 1.65;
    margin-bottom: 32px; max-width: 800px;
  }
  .bullets {
    list-style: none; display: flex; flex-direction: column; gap: 14px;
  }
  .bullets li {
    font-family: 'Inter', sans-serif; font-size: 22px;
    color: rgba(247,243,238,0.85); line-height: 1.5;
    display: flex; gap: 12px; align-items: flex-start;
  }
  .bullets .arrow { color: #C9A847; flex-shrink: 0; }
  .footer {
    position: absolute; bottom: 48px; left: 80px; right: 80px;
    display: flex; justify-content: space-between; align-items: center;
  }
  .footer-handle {
    font-family: 'Inter', sans-serif; font-size: 18px;
    color: rgba(247,243,238,0.4);
  }
  .footer-url {
    font-family: 'Inter', sans-serif; font-size: 16px;
    color: rgba(247,243,238,0.3);
  }
  .logo {
    position: absolute; bottom: 48px; right: 56px;
    font-family: 'Playfair Display', serif; font-size: 28px;
    font-weight: 700; color: #C9A847;
  }
</style>
</head>
<body>
<div class="slide">
  <div class="eyebrow">{{CATEGORY}}</div>
  <h1 class="headline">{{HEADLINE}}</h1>
  <p class="body-text">{{BODY}}</p>
  <ul class="bullets">{{BULLETS}}</ul>
  <div class="footer">
    <span class="footer-handle">@alicebazdikian</span>
    <span class="footer-url">smallbusinessaicoach.com</span>
  </div>
  <span class="logo">AB</span>
</div>
</body>
</html>
```

- [ ] **Step 4: Create carousel_cover.html (1080x1350)**

```html
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;0,900;1,700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { width: 1080px; height: 1350px; overflow: hidden; }
  .slide {
    width: 1080px; height: 1350px;
    background: #7D2240; position: relative;
    display: flex; flex-direction: column;
    justify-content: flex-end;
    padding: 80px 80px 120px;
  }
  .logo {
    position: absolute; top: 52px; right: 60px;
    font-family: 'Playfair Display', serif; font-size: 32px;
    font-weight: 700; color: #C9A847;
  }
  .eyebrow {
    font-family: 'Inter', sans-serif; font-size: 18px; font-weight: 600;
    letter-spacing: 0.14em; text-transform: uppercase;
    color: #C9A847; margin-bottom: 20px;
  }
  .headline {
    font-family: 'Playfair Display', serif;
    font-size: 72px; font-weight: 900;
    color: #F7F3EE; line-height: 1.1;
    letter-spacing: -0.02em; margin-bottom: 16px;
  }
  .subtitle {
    font-family: 'Inter', sans-serif; font-size: 22px;
    color: rgba(247,243,238,0.55); line-height: 1.5;
    max-width: 700px;
  }
  .teaser {
    font-family: 'Inter', sans-serif; font-size: 20px;
    color: rgba(247,243,238,0.7); margin-top: 20px;
    font-weight: 500;
  }
</style>
</head>
<body>
<div class="slide">
  <span class="logo">AB</span>
  <div class="eyebrow">{{CATEGORY}}</div>
  <h1 class="headline">{{HEADLINE}}</h1>
  <p class="subtitle">{{SUBTITLE}}</p>
  <p class="teaser">{{TEASER}}</p>
</div>
</body>
</html>
```

- [ ] **Step 5: Create carousel_content.html (1080x1350)**

```html
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;0,900;1,700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { width: 1080px; height: 1350px; overflow: hidden; }
  .slide {
    width: 1080px; height: 1350px;
    background: #F7F3EE; position: relative;
    display: flex; flex-direction: column;
    padding: 80px 80px 100px;
  }
  .big-num {
    font-family: 'Playfair Display', serif;
    font-size: 180px; font-weight: 900;
    color: rgba(201,168,71,0.12); line-height: 1;
    margin-bottom: 10px;
  }
  .headline {
    font-family: 'Playfair Display', serif;
    font-size: 52px; font-weight: 700;
    color: #1C1C1C; line-height: 1.2;
    letter-spacing: -0.02em; margin-bottom: 16px;
  }
  .gold-bar {
    width: 100%; height: 3px;
    background: linear-gradient(90deg, #C9A847, transparent);
    border-radius: 2px; margin-bottom: 28px;
  }
  .body-text {
    font-family: 'Inter', sans-serif; font-size: 26px;
    color: #6B6560; line-height: 1.65;
    max-width: 850px;
  }
  .handle {
    position: absolute; bottom: 52px; left: 80px;
    font-family: 'Inter', sans-serif; font-size: 18px;
    color: rgba(107,101,96,0.5);
  }
</style>
</head>
<body>
<div class="slide">
  <div class="big-num">{{NUMBER}}</div>
  <h2 class="headline">{{TITLE}}</h2>
  <div class="gold-bar"></div>
  <p class="body-text">{{BODY}}</p>
  <span class="handle">@alicebazdikian</span>
</div>
</body>
</html>
```

- [ ] **Step 6: Create carousel_cta.html (1080x1350)**

```html
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;0,900;1,700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { width: 1080px; height: 1350px; overflow: hidden; }
  .slide {
    width: 1080px; height: 1350px;
    background: #7D2240; position: relative;
    display: flex; flex-direction: column;
    justify-content: center;
    padding: 80px 80px;
  }
  .eyebrow {
    font-family: 'Inter', sans-serif; font-size: 18px; font-weight: 600;
    letter-spacing: 0.12em; text-transform: uppercase;
    color: #C9A847; margin-bottom: 24px;
  }
  .headline {
    font-family: 'Playfair Display', serif;
    font-size: 64px; font-weight: 900;
    color: #F7F3EE; line-height: 1.15;
    letter-spacing: -0.02em; margin-bottom: 40px;
  }
  .headline .gold { color: #C9A847; font-style: italic; }
  .actions {
    list-style: none; display: flex; flex-direction: column; gap: 20px;
    margin-bottom: 48px;
  }
  .actions li {
    font-family: 'Inter', sans-serif; font-size: 24px;
    color: rgba(247,243,238,0.8); line-height: 1.5;
    display: flex; gap: 14px; align-items: flex-start;
  }
  .actions .arrow { color: #C9A847; flex-shrink: 0; font-weight: 700; }
  .cta-btn {
    display: inline-block; align-self: flex-start;
    background: #C9A847; color: #1C1C1C;
    padding: 18px 44px; border-radius: 100px;
    font-family: 'Inter', sans-serif; font-size: 22px; font-weight: 700;
    letter-spacing: 0.02em;
  }
  .logo {
    position: absolute; bottom: 52px; right: 60px;
    font-family: 'Playfair Display', serif; font-size: 32px;
    font-weight: 700; color: #C9A847;
  }
</style>
</head>
<body>
<div class="slide">
  <div class="eyebrow">Want this for your business?</div>
  <h1 class="headline">Stop doing admin.<br>Start building <span class="gold">systems.</span></h1>
  <ul class="actions">
    <li><span class="arrow">→</span>Take the free AI Readiness Scorecard</li>
    <li><span class="arrow">→</span>Book a free 30-min AI diagnostic</li>
    <li><span class="arrow">→</span>Follow @alicebazdikian for daily AI tips</li>
  </ul>
  <div class="cta-btn">Link in Bio</div>
  <span class="logo">AB</span>
</div>
</body>
</html>
```

- [ ] **Step 7: Commit**

```bash
git add social-pipeline/templates/
git commit -m "feat: add branded HTML templates for social media graphics"
```

---

### Task 2: Build the Playwright rendering engine

**Files:**
- Create: `social-pipeline/render_graphics.py`
- Modify: `social-pipeline/requirements.txt`

- [ ] **Step 1: Add playwright to requirements.txt**

Append to `social-pipeline/requirements.txt`:
```
playwright>=1.40.0
```

- [ ] **Step 2: Install playwright and browsers**

```bash
cd "/Users/alicebazidian/Desktop/AI Project/AI Services Website/social-pipeline"
source venv/bin/activate
pip install playwright
playwright install chromium
```

- [ ] **Step 3: Create render_graphics.py**

```python
"""
Render branded HTML templates to PNG (single images) and PDF (carousels)
using Playwright headless Chromium.
"""

import os
import re
import json
from playwright.sync_api import sync_playwright
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
    # Preserve trailing punctuation
    trailing = ""
    if headline[-1] in ".!?":
        trailing = headline[-1]
    return f'{rest} <span class="gold">{last_word}</span>{trailing}'


def _bullets_html(caption):
    """Extract → bullet lines from caption text and wrap in <li> tags."""
    lines = caption.split("\n")
    bullets = []
    for line in lines:
        line = line.strip()
        if line.startswith("→"):
            text = line.lstrip("→").strip()
            bullets.append(f'<li><span class="arrow">→</span>{text}</li>')
    if not bullets:
        # Fallback: use first 3 non-empty lines
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
    # Extract first sentence of summary as body
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
    # Build teaser from carousel points count
    points_count = len(carousel_points)
    html = html.replace("{{TEASER}}", f"{points_count} key insights inside →")
    cover_path = os.path.join(output_dir, "slide-00-cover.png")
    _render_png(html, cover_path, 1080, 1350)
    slide_paths.append(cover_path)

    # Content slides
    for i, point in enumerate(carousel_points):
        html = _read_template("carousel_content.html")
        html = html.replace("{{NUMBER}}", point.get("number", f"{i+1:02d}"))
        html = html.replace("{{TITLE}}", point.get("title", ""))
        html = html.replace("{{BODY}}", point.get("body", ""))
        slide_path = os.path.join(output_dir, f"slide-{i+1:02d}-content.png")
        _render_png(html, slide_path, 1080, 1350)
        slide_paths.append(slide_path)

    # CTA slide
    cta_path = os.path.join(output_dir, "slide-99-cta.png")
    cta_html = _read_template("carousel_cta.html")
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
        # Wait for fonts to load
        page.wait_for_timeout(1500)
        page.screenshot(path=output_path, full_page=False)
        browser.close()

    print(f"  [Render] {os.path.basename(output_path)} ({width}x{height})")
    return output_path


def _combine_pngs_to_pdf(png_paths, pdf_path):
    """Combine multiple PNG slide images into a single PDF."""
    from PIL import Image

    images = []
    for path in png_paths:
        img = Image.open(path).convert("RGB")
        images.append(img)

    if images:
        images[0].save(pdf_path, save_all=True, append_images=images[1:], resolution=150)
        print(f"  [PDF] {os.path.basename(pdf_path)} ({len(images)} pages)")

    return pdf_path


def render_post(item, output_dir):
    """Render all graphics for a single post item.
    Returns dict with paths: {"png": "...", "pdf": "..." or None}
    """
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
    # Test with sample data
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
```

- [ ] **Step 4: Install Pillow for PDF generation**

```bash
cd "/Users/alicebazidian/Desktop/AI Project/AI Services Website/social-pipeline"
source venv/bin/activate
pip install Pillow
```

Add to `requirements.txt`:
```
Pillow>=10.0.0
```

- [ ] **Step 5: Test the renderer**

```bash
cd "/Users/alicebazidian/Desktop/AI Project/AI Services Website/social-pipeline"
source venv/bin/activate
python3 render_graphics.py
```

Expected: creates `output/test-render/` with `instagram-1080x1080.png` + `linkedin-carousel.pdf` (4 pages).

- [ ] **Step 6: Commit**

```bash
git add social-pipeline/render_graphics.py social-pipeline/requirements.txt
git commit -m "feat: add Playwright rendering engine for branded graphics"
```

---

### Task 3: Update draft_posts.py to generate carousel_points

**Files:**
- Modify: `social-pipeline/draft_posts.py`

- [ ] **Step 1: Update the system prompt output format**

In `draft_posts.py`, find the OUTPUT FORMAT section in `SYSTEM_PROMPT` and update to include `carousel_points`:

Find:
```
"category": "one of the 5 categories"
}
```

Replace with:
```
"category": "one of the 5 categories",
"carousel_points": [
  {"number": "01", "title": "short point title", "body": "2-3 sentence explanation"},
  {"number": "02", "title": "short point title", "body": "2-3 sentence explanation"},
  {"number": "03", "title": "short point title", "body": "2-3 sentence explanation"}
]
}

CAROUSEL POINTS: For every item (except "engagement" category), break the story into 2-3 key points for LinkedIn carousel slides. Each point should have a punchy title and a 2-3 sentence body. These become the numbered content slides.
```

- [ ] **Step 2: Commit**

```bash
git add social-pipeline/draft_posts.py
git commit -m "feat: add carousel_points to draft output schema"
```

---

### Task 4: Update run_pipeline.py to save digest data

**Files:**
- Modify: `social-pipeline/run_pipeline.py`
- Modify: `social-pipeline/send_email.py`
- Modify: `social-pipeline/config.py`

- [ ] **Step 1: Add digest_data paths to config.py**

Add to `config.py` after the `OUTPUT_DIR` line:

```python
DIGEST_DATA_DIR = os.path.join(BASE_DIR, "digest_data")
LATEST_DIGEST_FILE = os.path.join(DIGEST_DATA_DIR, "latest_digest.json")
LAST_THREAD_FILE = os.path.join(DIGEST_DATA_DIR, "last_thread_id.txt")
PROCESSED_REPLIES_FILE = os.path.join(DIGEST_DATA_DIR, "processed_replies.json")
```

- [ ] **Step 2: Update send_email.py to return thread ID**

In `send_email.py`, update the `send_email` function to also return the thread ID. Change the return line from:

```python
    return sent["id"]
```

to:

```python
    return sent["id"], sent.get("threadId", "")
```

- [ ] **Step 3: Update run_pipeline.py to save digest data and thread ID**

Add these imports at the top of `run_pipeline.py`:

```python
from config import DIGEST_DATA_DIR, LATEST_DIGEST_FILE, LAST_THREAD_FILE
```

After the `send_email()` call, add:

```python
    # Save digest data for template generation
    os.makedirs(DIGEST_DATA_DIR, exist_ok=True)
    with open(LATEST_DIGEST_FILE, "w") as f:
        json.dump(drafted_items, f, indent=2)
    print(f"[Data] Saved {len(drafted_items)} items to {LATEST_DIGEST_FILE}")

    # Save thread ID for reply detection
    with open(LAST_THREAD_FILE, "w") as f:
        f.write(thread_id)
    print(f"[Data] Thread ID saved: {thread_id}")
```

Also update the `send_email` call to capture both return values:

```python
    msg_id, thread_id = send_email(subject, html)
```

- [ ] **Step 4: Commit**

```bash
git add social-pipeline/config.py social-pipeline/send_email.py social-pipeline/run_pipeline.py
git commit -m "feat: save digest data and thread ID for template generation"
```

---

### Task 5: Build Google Drive uploader

**Files:**
- Create: `social-pipeline/upload_drive.py`
- Modify: `social-pipeline/gmail_auth.py`

- [ ] **Step 1: Add Drive scope to gmail_auth.py**

In `gmail_auth.py`, update the SCOPES list:

```python
SCOPES = [
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/drive.file",
]
```

Also add a `get_drive_service()` function after `get_gmail_service()`:

```python
def get_drive_service():
    """Return an authenticated Google Drive API service instance."""
    creds = _get_creds()
    return build("drive", "v3", credentials=creds)
```

And refactor the credential logic into a shared `_get_creds()` function used by both `get_gmail_service()` and `get_drive_service()`. Extract the credential loading/refresh logic into `_get_creds()`, then have both service functions call it.

- [ ] **Step 2: Delete token.json to force re-auth with new scope**

```bash
rm "/Users/alicebazidian/Desktop/AI Project/AI Services Website/social-pipeline/token.json"
cd "/Users/alicebazidian/Desktop/AI Project/AI Services Website/social-pipeline"
source venv/bin/activate
python3 gmail_auth.py
```

This will open a browser for re-authentication with the added Drive scope.

- [ ] **Step 3: Create upload_drive.py**

```python
"""
Upload graphics to Google Drive, organized by week.
"""

import os
from datetime import datetime
from gmail_auth import get_drive_service
from config import ALICE_EMAIL

# Set this to your Google Drive folder ID for "Social Media Content"
# Find it in the URL when you open the folder: drive.google.com/drive/folders/FOLDER_ID
DRIVE_PARENT_FOLDER_ID = os.environ.get("DRIVE_FOLDER_ID", "")


def _find_or_create_folder(service, name, parent_id=None):
    """Find a folder by name under parent, or create it."""
    query = f"name='{name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    if parent_id:
        query += f" and '{parent_id}' in parents"

    results = service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get("files", [])

    if files:
        return files[0]["id"]

    # Create folder
    metadata = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder",
    }
    if parent_id:
        metadata["parents"] = [parent_id]

    folder = service.files().create(body=metadata, fields="id").execute()
    print(f"  [Drive] Created folder: {name}")
    return folder["id"]


def _upload_file(service, file_path, folder_id):
    """Upload a single file to a Drive folder."""
    from googleapiclient.http import MediaFileUpload

    filename = os.path.basename(file_path)
    mime_types = {
        ".png": "image/png",
        ".pdf": "application/pdf",
    }
    ext = os.path.splitext(filename)[1].lower()
    mime_type = mime_types.get(ext, "application/octet-stream")

    metadata = {
        "name": filename,
        "parents": [folder_id],
    }
    media = MediaFileUpload(file_path, mimetype=mime_type)
    uploaded = service.files().create(
        body=metadata, media_body=media, fields="id, webViewLink"
    ).execute()

    print(f"  [Drive] Uploaded: {filename}")
    return uploaded.get("webViewLink", "")


def upload_post_graphics(post_dir, post_slug, week_label=None):
    """Upload all graphics in a post directory to Google Drive.
    Returns the Drive folder URL.
    """
    if not DRIVE_PARENT_FOLDER_ID:
        print("[WARN] DRIVE_FOLDER_ID not set — skipping Drive upload")
        return None

    service = get_drive_service()

    # Create week folder
    if not week_label:
        week_label = f"Week of {datetime.now().strftime('%Y-%m-%d')}"
    week_folder_id = _find_or_create_folder(service, week_label, DRIVE_PARENT_FOLDER_ID)

    # Create post folder
    post_folder_id = _find_or_create_folder(service, post_slug, week_folder_id)

    # Upload all files in the post directory
    links = []
    for filename in sorted(os.listdir(post_dir)):
        filepath = os.path.join(post_dir, filename)
        if os.path.isfile(filepath) and not filename.startswith("."):
            link = _upload_file(service, filepath, post_folder_id)
            links.append(link)

    # Return folder link
    folder_url = f"https://drive.google.com/drive/folders/{post_folder_id}"
    return folder_url


if __name__ == "__main__":
    print("Google Drive uploader ready.")
    if DRIVE_PARENT_FOLDER_ID:
        service = get_drive_service()
        print(f"Authenticated. Parent folder: {DRIVE_PARENT_FOLDER_ID}")
    else:
        print("Set DRIVE_FOLDER_ID env var to enable uploads.")
```

- [ ] **Step 4: Commit**

```bash
git add social-pipeline/gmail_auth.py social-pipeline/upload_drive.py
git commit -m "feat: add Google Drive uploader with folder organization"
```

---

### Task 6: Build reply monitor and orchestrator

**Files:**
- Create: `social-pipeline/monitor_reply.py`
- Create: `social-pipeline/generate_from_reply.py`

- [ ] **Step 1: Create monitor_reply.py**

```python
"""
Monitor Gmail for replies to the weekly digest email.
Parses selected post numbers from the reply body.
"""

import os
import re
import json
import base64
from gmail_auth import get_gmail_service
from config import LAST_THREAD_FILE, PROCESSED_REPLIES_FILE, DIGEST_DATA_DIR


def _load_thread_id():
    """Load the thread ID of the last digest email."""
    try:
        with open(LAST_THREAD_FILE) as f:
            return f.read().strip()
    except FileNotFoundError:
        return None


def _load_processed():
    """Load set of already-processed reply message IDs."""
    try:
        with open(PROCESSED_REPLIES_FILE) as f:
            return set(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()


def _save_processed(processed):
    """Save processed reply IDs."""
    os.makedirs(DIGEST_DATA_DIR, exist_ok=True)
    with open(PROCESSED_REPLIES_FILE, "w") as f:
        json.dump(list(processed), f)


def _parse_numbers(text):
    """Extract post numbers from reply text. Handles '1, 3, 5, 7' or '1 3 5 7'."""
    # Remove common prefixes
    text = re.sub(r'(?i)(items?|posts?|numbers?|picks?)[:\s]*', '', text)
    # Find all numbers
    numbers = [int(n) for n in re.findall(r'\d+', text)]
    # Filter reasonable range (1-20)
    return [n for n in numbers if 1 <= n <= 20]


def check_for_reply():
    """Check if there's a new reply to the digest thread.
    Returns list of selected item indices (0-based) or None.
    """
    thread_id = _load_thread_id()
    if not thread_id:
        print("[Monitor] No thread ID found — no digest sent yet?")
        return None

    processed = _load_processed()
    service = get_gmail_service()

    try:
        thread = service.users().threads().get(userId="me", id=thread_id).execute()
        messages = thread.get("messages", [])

        if len(messages) < 2:
            print("[Monitor] No reply yet")
            return None

        # Check replies (skip first message = the digest itself)
        for msg in messages[1:]:
            msg_id = msg["id"]
            if msg_id in processed:
                continue

            # Get message body
            payload = msg.get("payload", {})
            body_text = ""

            # Try plain text first
            if payload.get("body", {}).get("data"):
                body_text = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="ignore")
            else:
                # Check parts
                for part in payload.get("parts", []):
                    if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
                        body_text = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="ignore")
                        break

            if not body_text:
                continue

            numbers = _parse_numbers(body_text)
            if numbers:
                # Mark as processed
                processed.add(msg_id)
                _save_processed(processed)
                print(f"[Monitor] Found reply with picks: {numbers}")
                # Convert to 0-based indices
                return [n - 1 for n in numbers]
            else:
                print(f"[Monitor] Reply found but no numbers parsed from: {body_text[:100]}")
                processed.add(msg_id)
                _save_processed(processed)

    except Exception as e:
        print(f"[Monitor] Error checking thread: {e}")

    return None


if __name__ == "__main__":
    result = check_for_reply()
    if result:
        print(f"Selected items (0-based): {result}")
    else:
        print("No actionable reply found.")
```

- [ ] **Step 2: Create generate_from_reply.py**

```python
"""
Orchestrator: parse reply → load digest → render graphics → upload to Drive → send confirmation.
"""

import os
import json
import re
from datetime import datetime

from config import LATEST_DIGEST_FILE, OUTPUT_DIR, ALICE_EMAIL
from monitor_reply import check_for_reply
from render_graphics import render_post
from upload_drive import upload_post_graphics
from send_email import send_email


def _slugify(text):
    """Convert headline to a URL-safe slug."""
    text = text.lower().strip()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s]+', '-', text)
    return text[:50].rstrip('-')


def _load_digest():
    """Load the latest digest items."""
    try:
        with open(LATEST_DIGEST_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"[ERROR] Could not load digest: {e}")
        return []


def generate_graphics(selected_indices=None):
    """Generate graphics for selected items. If no indices, check for reply."""
    if selected_indices is None:
        selected_indices = check_for_reply()
        if not selected_indices:
            print("[Generate] No reply with picks found. Nothing to do.")
            return

    items = _load_digest()
    if not items:
        print("[Generate] No digest data found.")
        return

    week_label = f"Week of {datetime.now().strftime('%Y-%m-%d')}"
    week_dir = os.path.join(OUTPUT_DIR, week_label.replace(" ", "-").lower())
    os.makedirs(week_dir, exist_ok=True)

    generated = []
    drive_links = []

    for idx in selected_indices:
        if idx < 0 or idx >= len(items):
            print(f"[WARN] Index {idx} out of range (0-{len(items)-1}), skipping")
            continue

        item = items[idx]
        slug = f"{idx+1}-{_slugify(item.get('headline', 'post'))}"
        post_dir = os.path.join(week_dir, slug)

        print(f"\n--- Rendering: {item.get('headline', '')} ---")

        try:
            result = render_post(item, post_dir)
            generated.append({
                "index": idx + 1,
                "headline": item.get("headline", ""),
                "png": result["png"],
                "pdf": result["pdf"],
            })

            # Upload to Drive
            drive_url = upload_post_graphics(post_dir, slug, week_label)
            if drive_url:
                drive_links.append({"headline": item.get("headline", ""), "url": drive_url})

        except Exception as e:
            print(f"[ERROR] Failed to render '{item.get('headline', '')}': {e}")
            continue

    # Send confirmation email
    if generated:
        _send_confirmation(generated, drive_links)

    print(f"\n{'='*60}")
    print(f"DONE — {len(generated)} posts rendered")
    print(f"{'='*60}")


def _send_confirmation(generated, drive_links):
    """Send confirmation email with list of generated graphics."""
    items_html = ""
    for g in generated:
        drive_link = ""
        for dl in drive_links:
            if dl["headline"] == g["headline"]:
                drive_link = f' · <a href="{dl["url"]}" style="color:#C9A847;">View in Drive</a>'
                break
        items_html += f"""
        <tr><td style="padding:8px 0;border-bottom:1px solid rgba(28,28,28,0.06);">
          <span style="font-weight:600;color:#1C1C1C;">{g['index']}. {g['headline']}</span>
          <span style="font-size:12px;color:#6B6560;"> — PNG{'+ PDF' if g['pdf'] else ''}{drive_link}</span>
        </td></tr>"""

    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#F7F3EE;font-family:Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#F7F3EE;">
<tr><td align="center" style="padding:32px 16px;">
<table width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;">
  <tr><td style="text-align:center;padding:0 0 24px;">
    <p style="font-family:Georgia,serif;font-size:22px;font-weight:700;color:#7D2240;margin:0 0 4px;">AB</p>
    <h1 style="font-family:Georgia,serif;font-size:24px;font-weight:700;color:#1C1C1C;margin:0;">Your graphics are ready</h1>
    <p style="font-size:13px;color:#6B6560;margin:4px 0 0;">{len(generated)} posts · {datetime.now().strftime('%B %d, %Y')}</p>
  </td></tr>
  <tr><td><div style="height:2px;background:linear-gradient(90deg,#7D2240,#C9A847);border-radius:2px;margin-bottom:20px;"></div></td></tr>
  <tr><td>
    <table width="100%" cellpadding="0" cellspacing="0">{items_html}</table>
  </td></tr>
  <tr><td style="text-align:center;padding:24px 0 0;">
    <p style="font-size:13px;color:#6B6560;">Graphics saved locally and uploaded to Google Drive.</p>
  </td></tr>
</table>
</td></tr>
</table>
</body></html>"""

    try:
        send_email(f"Your graphics are ready — {len(generated)} posts", html)
    except Exception as e:
        print(f"[WARN] Confirmation email failed: {e}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        # Manual mode: python3 generate_from_reply.py 1 3 5 7
        indices = [int(n) - 1 for n in sys.argv[1:]]
        generate_graphics(indices)
    else:
        # Auto mode: check for reply
        generate_graphics()
```

- [ ] **Step 3: Commit**

```bash
git add social-pipeline/monitor_reply.py social-pipeline/generate_from_reply.py
git commit -m "feat: add reply monitor and graphics generation orchestrator"
```

---

### Task 7: End-to-end test

- [ ] **Step 1: Run the content pipeline to generate digest data**

```bash
cd "/Users/alicebazidian/Desktop/AI Project/AI Services Website/social-pipeline"
source venv/bin/activate
ANTHROPIC_API_KEY="..." python3 run_pipeline.py
```

Verify: `digest_data/latest_digest.json` and `digest_data/last_thread_id.txt` are created.

- [ ] **Step 2: Test graphic rendering manually**

```bash
python3 generate_from_reply.py 1 2 3
```

This renders graphics for items 1, 2, 3 from the latest digest. Check `output/` for the PNG and PDF files.

- [ ] **Step 3: Open generated files and verify**

Check that:
- PNG files are 1080x1080 with burgundy background, correct fonts, gold accents
- PDF carousels have 4+ pages at 1080x1350
- CTA slide is the last page of every carousel

- [ ] **Step 4: Commit final state**

```bash
git add -A
git commit -m "feat: complete social media template system — end-to-end tested"
```
