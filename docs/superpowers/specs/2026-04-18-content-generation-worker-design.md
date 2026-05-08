# Content Generation Worker — Design Spec

## Context

The Content Hub dashboard (shipped 2026-04-18) lets Alice pick competitor posts per channel and enqueues a "Create" job. `jobs/create_worker.py` is currently a stub that flips jobs queued → done without producing anything. This spec covers turning that stub into the real drafting + rendering + Drive + email pipeline so Alice's Friday weekly workflow produces publish-ready files by end of day.

In scope: draft generation in Alice's voice, per-channel rendering to final formats, Google Drive weekly folder, rich HTML approval email, "Done" reply → final files in `/READY-TO-POST/`. Out of scope: auto-posting to social platforms, monthly activation, DM automation.

## Decisions (from brainstorming)

1. **One draft per selected post**, 1-to-1. IG + TT merged into a single "Short-form social" tab — one table, one Create button, drafts rendered for both IG and TT formats from the same script.
2. **Voice capture from 5–10 Alice-written posts** (she'll paste them before build; extracted patterns go into the drafter system prompt as few-shot + rules).
3. **Drive layout:** `/Content Hub/<week_id>/{youtube,linkedin,social}/` + root `SUMMARY.md` index.
4. **Rich HTML weekly digest email** (one per week, all channels inline) + **strict `Done` reply parsing** (first word == "done", case-insensitive).
5. **Final files only, manual post.** After `Done`, worker re-renders edited Drive content → `/<week_id>/READY-TO-POST/`; Alice posts manually.
6. **YouTube output:** Google Slides deck only (Google Slides API), brand-styled, Alice name + website on every slide.
7. **Carousel rendering reuses `social-pipeline/render_graphics.py`** (already does HTML → Playwright → JPG).

## Open items needed from Alice before build

- 5–10 links to her best-performing posts (LinkedIn + IG/TT mix) for voice extraction.
- Confirm which existing carousel HTML template in `social-pipeline/templates/` is the "approved" one (candidates: `carousel_cover.html`, `carousel_content.html`, `carousel_cta.html`, `quote_hook.html`).
- Google service account + Drive folder ID for the `/Content Hub/` root (or OAuth creds if preferring personal Drive).
- Confirm preferred caption length ranges per channel (default proposed: IG ≤150 words, TT ≤80, LI ≤220).

## Architecture

```
content_hub/
├── jobs/
│   └── create_worker.py            (stub today → full orchestrator after this spec)
├── generate/                       (NEW)
│   ├── __init__.py
│   ├── voice.py                    Loads Alice voice profile; exposes VOICE_SYSTEM_PROMPT
│   ├── draft.py                    Per-channel draft generator (Claude Sonnet 4.6 calls)
│   ├── fingerprint.py              Topic fingerprint for IG+TT dedupe
│   └── captions.py                 CTA selector + hashtag composer
├── render/                         (NEW)
│   ├── __init__.py
│   ├── carousel_jpg.py             HTML → Playwright → JPG (wraps social-pipeline/render_graphics)
│   ├── carousel_video.py           5-sec-per-slide JPG→MP4 via ffmpeg
│   ├── linkedin_pdf.py             HTML → PDF carousel
│   └── yt_slides.py                Google Slides API deck creator
├── drive/                          (NEW)
│   ├── __init__.py
│   ├── client.py                   Reuses social-pipeline/upload_drive.py creds
│   ├── layout.py                   Week folder builder + SUMMARY.md writer
│   └── watch.py                    Polls edited Drive files for Done-reply re-render
├── email_digest/                   (NEW)
│   ├── __init__.py
│   ├── render.py                   Jinja HTML email (reuses brand tokens)
│   ├── send.py                     Reuses social-pipeline/send_email.py
│   └── reply_parser.py             Strict `done` parser; hooks social-pipeline/monitor_reply.py
└── voice_samples/                  (NEW, .gitignored)
    └── alice_posts.md              5-10 pasted posts for voice extraction
```

## Reuse from existing codebase

- `social-pipeline/render_graphics.py` — HTML → JPG pipeline. `render/carousel_jpg.py` imports its `render_to_jpg(html, out_path)`.
- `social-pipeline/templates/carousel_*.html` — existing approved templates; `render/carousel_jpg.py` fills them with `{hook, body, cta, slide_n, total, website}`.
- `social-pipeline/upload_drive.py` — Drive OAuth client; `drive/client.py` imports its `get_service()`.
- `social-pipeline/send_email.py` — Gmail send wrapper; `email_digest/send.py` imports `send_html(to, subject, html)`.
- `social-pipeline/monitor_reply.py` — Gmail reply polling; `email_digest/reply_parser.py` subscribes to its on-new-reply hook.
- `social-pipeline/gmail_auth.py` — shared OAuth creds.
- Brand tokens from `content_hub/static/style.css` — extracted to `BRAND` dict; reused for slide + email HTML.
- `content_hub/config.py` — `ANTHROPIC_API_KEY`, Alice email; add `DRAFTER_MODEL = "claude-sonnet-4-6"`, `SLIDES_MODEL = "claude-haiku-4-5"`.

## Data flow

```
Friday workflow:
  scheduler.py (Friday 8am)  → posts in hub.db  (shipped)
  Alice reviews dashboard    → ticks checkboxes, pastes URLs, clicks Create per channel (shipped)
  enqueue_job(payload)       → jobs row status='queued'                                   (shipped)

  create_worker.py picks job:
    1. Load selected posts + pasted URLs from hub.db
    2. For pasted URLs without a post row → hit per-channel fetcher on-demand
    3. For "social" channel jobs (IG+TT combined):
         fingerprint.dedupe(selected) → drop near-duplicates
    4. For each post → draft.generate_draft(post, channel, voice=VOICE)
         → Claude Sonnet 4.6, caption + carousel slides structure (cover/content×N/cta)
    5. Render per channel:
         • YT: render/yt_slides.create_deck(draft) → Google Slides URL
         • LI: render/linkedin_pdf.make_pdf(draft)
         • social: render/carousel_jpg.make_slides(draft) + carousel_video.make_mp4(slides)
    6. Upload to /Content Hub/<week_id>/<channel>/ via drive/client
    7. Write /Content Hub/<week_id>/SUMMARY.md (all drafts + hooks + Drive links)
    8. email_digest/render.html_for_week(week_id) → send.send_html(to=Alice)
    9. jobs row → status='awaiting_approval', result_json holds Drive URLs

  Alice edits drafts directly in Drive, replies "Done" to email:
    monitor_reply catches reply → reply_parser.is_done(body)=True
    → worker triggered: read edited Drive files, re-render to final format,
      write to /<week_id>/READY-TO-POST/ subfolder
    → second email: "Ready to post. N files in /READY-TO-POST/"
    → jobs row → status='done'
```

## Voice profile (`generate/voice.py`)

- Reads `content_hub/voice_samples/alice_posts.md` (5–10 posts provided by Alice).
- At build-time (one-off): runs a Claude Opus prompt that extracts:
  - 3–5 signature opener patterns
  - Avg. sentence length, line-break rhythm (e.g. single-line stanzas)
  - Emoji usage rate + preferred ones
  - CTA placement (inline / last line / second-to-last)
  - Do-say / don't-say word list
  - Sample hooks (verbatim, used as few-shot)
- Persists to `content_hub/voice_samples/voice_profile.yaml` (checked in, editable).
- `VOICE_SYSTEM_PROMPT` is assembled from that YAML at worker boot.

Rebuild voice profile when Alice adds more sample posts: `python -m content_hub.generate.voice --rebuild`.

## Drafter (`generate/draft.py`)

- Input: source post row (+ normalized caption + hook + channel context) + channel = `youtube | linkedin | social`.
- Claude Sonnet 4.6 with `VOICE_SYSTEM_PROMPT` + channel-specific shape template (e.g. `"social" → 8-slide carousel: cover, 6 body, cta`).
- Returns a `Draft` dataclass:
  ```python
  Draft(
    source_post_id: str,
    channel: str,
    hook: str,
    slides: list[SlideContent],      # [{kind, title, body}]
    caption: str,
    cta: str,                        # picked from Active CTAs list
    hashtags: list[str],
  )
  ```
- Active CTAs (from marketing doc): `subscribe_newsletter`, `book_diagnostic`, `register_webinar`, `follow`, `dm_word`.

## CTA + hashtag composer (`generate/captions.py`)

- Round-robins CTA types across a batch so every draft doesn't end with the same CTA.
- Hashtags from `BRAND` constants in config: `HASHTAGS_BRANDED + HASHTAGS_NICHE + HASHTAGS_REACH` (reuses the list from `social-pipeline/config.py`).

## Drive layout (`drive/layout.py`)

```
/Content Hub/
└── 2026-04-13/
    ├── SUMMARY.md
    ├── youtube/
    │   └── 01-claude-plugins/
    │       ├── deck.gslide         (Google Slides URL)
    │       └── source.md           (link to source YT video + why-trending)
    ├── linkedin/
    │   └── 01-opus-47-review/
    │       ├── carousel.pdf
    │       ├── caption.md
    │       └── source.md
    ├── social/
    │   └── 01-vertical-hook/
    │       ├── slides/01.jpg … 08.jpg
    │       ├── carousel.mp4
    │       ├── caption.md
    │       └── source.md
    └── READY-TO-POST/              (created after Alice replies Done)
        └── ... (re-rendered from edited drafts)
```

## Email digest (`email_digest/render.py`)

- One `<section>` per channel, one `<div class="draft-card">` per draft containing:
  - Hook (large, Fraunces serif, burgundy)
  - Format tag + source creator @handle + source engagement (e.g. "3.4k ♥ · 18k 👁")
  - Caption preview (first 40 words)
  - `[Edit in Drive →]` primary button
  - `[Source post ↗]` secondary link
- Footer: "Reply **Done** when you've edited everything you want to publish."
- Brand styling from existing `content_hub/static/style.css` tokens (burgundy/gold/eggshell).

## Verification

1. **Unit** — `draft.generate_draft(fixture_post)` returns a complete `Draft` with ≤220-word caption + 8 slides + CTA + hashtags; snapshot-compared.
2. **Voice test** — run 3 test drafts; human-review against the 5-10 sample posts; refine `voice_profile.yaml` until blind test ("did Alice write this?") passes.
3. **Render** — `carousel_jpg.make_slides(draft)` outputs 8 JPGs matching brand; `linkedin_pdf.make_pdf` produces a valid 10-page PDF; `yt_slides.create_deck` produces a shareable Google Slides URL.
4. **Drive** — after a full dry-run job, `/Content Hub/<week_id>/SUMMARY.md` lists every draft with a working Drive link.
5. **Email** — digest renders in Gmail (test with abazdikian@gmail.com); HTML degrades gracefully in plain-text view.
6. **Done parsing** — 6 reply variants tested: `Done`, `done`, `DONE`, `Done!`, `Done thanks`, `Looks great` → first 5 match, last does not.
7. **End-to-end** — pick 2 posts in dashboard → Create → worker runs < 15 min → email arrives → edit 1 draft in Drive → reply Done → READY-TO-POST folder contains final files.

## Deferred to future specs

- Auto-posting to LinkedIn / IG / TT via APIs.
- Blog post card-image strategy (marketing doc mentions this).
- Monthly activation (podcasts, conferences, lead magnets).
- DM funnel word-trigger automation.
- Multi-variant A/B draft generation.

## Estimated build time

~1.5–2 working days:
- Day 1 AM: voice capture + drafter + CTA composer
- Day 1 PM: social carousel JPG + MP4 render + Drive uploader
- Day 2 AM: LinkedIn PDF + YouTube Slides API deck
- Day 2 PM: email digest + Done reply parser + end-to-end test
