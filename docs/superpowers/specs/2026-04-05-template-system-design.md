# Social Media Template System — Design Spec

## Overview

An automated graphic generation system that takes approved post drafts and renders branded PNG images (Instagram/Facebook) and multi-slide PDF carousels (LinkedIn), then uploads them to Google Drive. Triggered by replying to the weekly digest email with post numbers.

## Trigger Flow

```
You receive weekly digest email (Sunday 9am ET)
    │
    ▼
You reply with picks: "1, 3, 5, 7"
    │
    ▼
Gmail API detects reply (polling or push)
    │
    ▼
Parse selected item numbers from reply
    │
    ▼
Load drafted items from latest digest (stored as JSON)
    │
    ▼
For each selected item:
    ├── Render single-image PNG (1080x1080) for IG/FB
    ├── Render multi-slide PDF (1080x1350 per slide) for LinkedIn
    └── Upload both to Google Drive
    │
    ▼
Send confirmation email: "7 graphics ready in your Drive folder"
```

## Template Types

### 1. Quote/Hook (single image — 1080x1080)
**Used for:** `thought-leadership`, `engagement`

- Burgundy `#7D2240` background
- Centered layout
- Category label top-left + "QUOTES" or category top-right (small uppercase)
- Large serif headline (Playfair Display) — main hook text
- One key word in gold `#C9A847` italic for emphasis
- Handle in pill badge at bottom center (`@alicebazdikian`)
- AB logo bottom-right corner

### 2. Text/Announcement (single image — 1080x1080)
**Used for:** `ai-news`, `how-to`, `promo`

- Burgundy `#7D2240` background
- Left-aligned layout
- Small category eyebrow top-left (gold, uppercase)
- Large bold headline (mix of bold + light weight for contrast)
- Body paragraph below (eggshell text, 0.85 opacity)
- 3-4 value bullets with → arrows
- Handle + URL in footer
- AB logo bottom-right corner

### 3. Carousel Cover (first slide of LinkedIn PDF — 1080x1350)
**Used for:** all categories except `engagement`

- Burgundy `#7D2240` background
- AB logo top-right
- Gold eyebrow category label (e.g., "AI FOR BUSINESS")
- Large serif headline (Playfair Display, eggshell text)
- Subtitle line below (smaller, 0.6 opacity)
- Summary stat or teaser (e.g., "3 tools. $0/month. 12 hours saved.")

### 4. Carousel Content Slide (middle slides — 1080x1350)
**Used for:** all carousels

- Eggshell `#F7F3EE` background
- Large watermark number top-left (e.g., "01", "02", "03") in faint gold `rgba(201,168,71,0.15)`
- Bold serif headline (Playfair Display, charcoal)
- Gold gradient divider bar below headline
- Body paragraph (Inter, muted color, 1.5 line-height)
- Handle at bottom

### 5. Carousel CTA Slide (last slide — 1080x1350)
**Used for:** all carousels (final slide)

- Burgundy `#7D2240` background
- Gold eyebrow: "Want this for your business?"
- Bold serif hook headline with gold italic accent word
- 3 action items with → arrows:
  - "Take the free AI Readiness Scorecard"
  - "Book a free 30-min AI diagnostic"
  - "Follow @alicebazdikian for daily AI tips"
- Gold "Link in Bio" button (pill shape)
- AB logo bottom-right

## Auto-Selection Rules

| Content Category | Single Image Template | Carousel? |
|---|---|---|
| `ai-news` | Text/Announcement | Yes (3-5 slides) |
| `how-to` | Text/Announcement | Yes (3-5 slides) |
| `thought-leadership` | Quote/Hook | Yes (3-5 slides) |
| `engagement` | Quote/Hook | No (single image only) |
| `promo` | Text/Announcement | Yes (3-5 slides) |

## Carousel Slide Content Generation

For carousel content slides (the numbered middle slides), the system takes the post's caption and breaks it into 2-3 content cards. The Claude API call that originally drafted the post also generates `carousel_points` — an array of 2-3 objects:

```json
{
  "carousel_points": [
    {"number": "01", "title": "Claude for Email + Proposals", "body": "Draft client emails in 30 seconds..."},
    {"number": "02", "title": "Notion AI for Meeting Notes", "body": "Record, transcribe, and summarize..."},
    {"number": "03", "title": "Calendly + Zapier for Scheduling", "body": "Clients book themselves..."}
  ]
}
```

This means the `draft_posts.py` module needs to be updated to also generate `carousel_points` for each item.

## Output Format

### Single Image
- Format: PNG
- Dimensions: 1080x1080 pixels
- One file per post

### LinkedIn Carousel
- Format: PDF (multi-page)
- Dimensions: 1080x1350 pixels per page
- Pages: Cover + 2-3 content slides + CTA slide = 4-6 pages total
- Not generated for `engagement` category posts

## Google Drive Structure

```
Social Media Content/
└── Week of 2026-04-06/
    ├── 1-i-fired-my-va/
    │   ├── instagram-1080x1080.png
    │   └── linkedin-carousel.pdf
    ├── 3-stop-doing-admin/
    │   ├── instagram-1080x1080.png
    │   └── linkedin-carousel.pdf
    ├── 5-free-ai-tools/
    │   ├── instagram-1080x1080.png
    │   └── linkedin-carousel.pdf
    └── 7-poll-ai-for-proposals/
        └── instagram-1080x1080.png  (no carousel for engagement posts)
```

## Brand System

### Colors
- Background: Burgundy `#7D2240`
- Text: Eggshell `#F7F3EE`
- Accent: Gold `#C9A847`
- Dark burgundy: `#651B33` (hover states, shadows)
- Deep burgundy: `#3D1020` (gradients)
- Charcoal: `#1C1C1C` (text on light backgrounds)
- Muted: `#6B6560` (secondary text)

### Typography
- Headlines: Playfair Display (serif), 700/900 weight
- Body: Inter (sans-serif), 400/500 weight
- Loaded via Google Fonts in the HTML templates

### Assets
- AB logo: `Thumbnail logo.png` (gold on burgundy monogram)
- Headshot: `Brand Assets/_MCK3991.jpg` (used only if needed)

### Consistent Elements on Every Graphic
- AB logo in corner
- @alicebazdikian handle
- smallbusinessaicoach.com URL (on CTA slides)
- Gold accent (either divider, eyebrow, or accent word)

## Technical Implementation

### Language
Python — same as the content pipeline, lives in `social-pipeline/`.

### New Files
```
social-pipeline/
├── templates/
│   ├── quote_hook.html          # Quote/Hook single image template
│   ├── text_announcement.html   # Text/Announcement single image template
│   ├── carousel_cover.html      # Carousel cover slide
│   ├── carousel_content.html    # Carousel content slide (reused per point)
│   └── carousel_cta.html        # Carousel CTA slide
├── render_graphics.py           # Playwright renders HTML → PNG/PDF
├── upload_drive.py              # Google Drive API upload
├── monitor_reply.py             # Gmail API polls for digest reply
├── generate_from_reply.py       # Orchestrator: parse reply → render → upload → confirm
└── digest_data/
    └── latest_digest.json       # Saved drafted items from last pipeline run
```

### Modified Files
- `draft_posts.py` — add `carousel_points` to output schema
- `run_pipeline.py` — save drafted items to `digest_data/latest_digest.json`
- `config.py` — add Google Drive folder ID, template paths

### Dependencies (new)
- `playwright` — headless browser for rendering HTML to PNG/PDF
- `google-auth`, `google-api-python-client` — Google Drive API (already installed for Gmail)

### Gmail Reply Detection
- `monitor_reply.py` polls Gmail for replies to the last digest thread
- Run via a second scheduled trigger: every 30 minutes on Sundays only (9am-11pm ET), to catch Alice's reply
- Matches by thread ID (saved to `digest_data/last_thread_id.txt` when digest is sent)
- Parses numbers from reply body (e.g., "1, 3, 5, 7" or "1 3 5 7" or "items 1, 3, 5, 7")
- If reply found and not yet processed, triggers `generate_from_reply.py` with selected item indices
- Marks reply as processed (saves message ID to `digest_data/processed_replies.json`) to avoid re-triggering

### Rendering Pipeline
For each selected item:
1. Determine template type based on category
2. Inject content (headline, caption, hashtags, carousel_points) into HTML template
3. Open HTML in Playwright headless browser
4. Screenshot at exact dimensions → save as PNG (single image)
5. For carousels: render cover + content slides + CTA → combine into PDF
6. Upload all files to Google Drive

### Google Drive Auth
Reuse the same OAuth credentials as Gmail (scopes need `https://www.googleapis.com/auth/drive.file` added). The `gmail_auth.py` module will be updated to include Drive scope.

### Confirmation Email
After all graphics are generated and uploaded, send a confirmation email to Alice:
- Subject: "Your graphics are ready — [N] posts in Drive"
- Body: list of posts with Drive folder link

## Error Handling
- If Playwright rendering fails for one item, skip it and continue with the rest
- If Drive upload fails, save files locally to `social-pipeline/output/` as fallback
- If no reply is detected within 48 hours of digest send, do nothing (no nagging)
- If reply contains no parseable numbers, send a clarification email: "I couldn't parse your picks. Reply with just the numbers (e.g., 1, 3, 5)"

## Success Criteria
- Reply to digest email → graphics appear in Drive within 5 minutes
- PNG images are crisp at 1080x1080 with correct brand colors and typography
- PDF carousels have 4-6 pages at 1080x1350, proper slide order
- Google Drive folder is organized by week with clear file naming
- Confirmation email links to the Drive folder
