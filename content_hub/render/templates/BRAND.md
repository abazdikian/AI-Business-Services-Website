# Content Hub — Brand Refresh v2

**These templates are the locked brand for the weekly content-marketing
pipeline.** Every Friday pull + draft + render + upload uses them. Changes
here ripple through every artifact — carousel, infographic, talking deck.

## Tokens (use these everywhere)

| Token             | Hex       | Use                                       |
|-------------------|-----------|-------------------------------------------|
| burgundy          | `#7A1530` | primary — titles on white, bg on dark     |
| burgundy-soft     | `#9B2440` | gradient mid-stop                         |
| burgundy-glow     | `#C13558` | gradient bright end, accents              |
| gold              | `#D4A84A` | elevated secondary — accents, handle      |
| gold-warm         | `#E6C472` | highlights, gradient end                  |
| gold-deep         | `#A87B1F` | gold on white (darker for contrast)       |
| white             | `#FFFFFF` | surface 1                                 |
| ink               | `#2B1A1F` | body text                                 |
| ink-soft          | `#6B5A5F` | secondary text                            |
| rule              | `#EFE8E3` | dividers                                  |

**Signature gradient:** `linear-gradient(135deg, burgundy 0%, burgundy-soft 65%, burgundy-glow 100%)`

## Type

- **Display:** `'Fraunces', Georgia, serif` — titles, eyebrows, monogram, accents
- **Body:** `'Nunito', system-ui, sans-serif` — copy, bullets, UI
- **Italic is a first-class brand signal** — use it for hooks, accent phrases, the monogram "ab", the signature line

## Monogram

- **Shape:** rounded-square (1.05" × 0.70" on 10" deck, 84×84px on carousels)
- **Letters:** lowercase italic "ab" in Fraunces 700
- On **burgundy** surfaces: gold tile, burgundy letters
- On **white** surfaces: burgundy tile, gold letters
- Position: top-right on most surfaces; top-left on full-bleed title/cover
  pages where it would collide with a centered title

## Templates managed by this brand

| Artifact            | File                                               | Sizes                   |
|---------------------|----------------------------------------------------|-------------------------|
| Carousel slide      | [slide.html](slide.html)                           | 4:5 (LI/IG) · 9:16 (TT) |
| Infographic         | [infographic.html](infographic.html) · [INFOGRAPHIC.md](INFOGRAPHIC.md) | 4:5 |
| YouTube talking deck| [../../notify/slides.py](../../notify/slides.py)   | 16:9 Slides             |

## Rules that apply everywhere

1. **No dark colors.** Burgundy is the darkest surface. Never black bg, never maroon, never deep burgundy.
2. **Gold is structural**, not decorative. Use it for accent bars, bullet dots, pill buttons, eyebrow labels, handle colors on burgundy surfaces.
3. **Editorial voice.** Polished. Sentence case. No lowercase titles, no trailing emoji swarms.
4. **One monogram per slide.** Never duplicate it.
5. **Footer handle** = `@smallbusinessaicoach` (uppercase `@SMALLBUSINESSAICOACH` on carousels/deck, mixed case on infographic).
6. **Italic signature line** = `Alice Bazdikian` in Fraunces italic (carousels + deck footer).

## Pipeline wiring

The weekly Friday cron (`content_hub/scheduler.py` → `content_hub/jobs/create_worker.py`):
1. Pulls top competitor posts per channel
2. Drafter (Sonnet, tool-use) writes Alice-voice slides + caption
3. Renders carousel PNGs via [carousel.py](../carousel.py) using `slide.html`
4. Builds LinkedIn PDF via [pdf.py](../pdf.py), TikTok MP4 via [video.py](../video.py)
5. For YouTube: fetches transcript, builds deck via [slides.py](../../notify/slides.py)
6. Uploads everything to Drive, emails Alice

Infographic is triggered separately (weekly) by calling `render_infographic()`
with a preset dict — not automated on every batch.

## Changing the brand

If you ever need to evolve this:
1. Update [slide.html](slide.html) CSS tokens + [infographic.html](infographic.html) CSS tokens + `BRAND_*` constants in [../../notify/slides.py](../../notify/slides.py) **in the same commit**.
2. Update this file + [INFOGRAPHIC.md](INFOGRAPHIC.md).
3. Smoke-test all three artifacts before merging.

Never update one template without the others — brand drift creates an inconsistent feed.
