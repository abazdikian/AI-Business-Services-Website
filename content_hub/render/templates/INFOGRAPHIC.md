# LinkedIn Weekly Infographic — Template

**Brand Refresh v2 — locked.** The file [infographic.html](infographic.html)
is the official template for the weekly LinkedIn infographic. Every future
infographic should use it so the visual language stays consistent.

## Brand rules (don't break these)

- **Palette:** burgundy `#7A1530` · gold `#D4A84A` · ink `#2B1A1F` · white · no dark colors
- **Lines / borders / accents:** burgundy (card top, dividers), gold (underline bar, accents)
- **Titles:** **Fraunces** (serif, 700 weight; italic for accent phrasing)
- **Body:** **Nunito** (sans, 500–800 weight)
- **Monogram:** CSS-rendered lowercase italic "ab" in a rounded-square tile —
  burgundy tile w/ gold letters on white slides
- **Size:** 1080 × 1350 (portrait, 4:5 — LinkedIn document carousel ratio)

## Layout

```
┌──────────────────────────────────────────────┐
│ [ab tile]                [• 10 · ESSENTIAL]  │   header
│                                              │
│  Topic Title   (with italic accent)          │   burgundy Fraunces
│  ──                                          │   gold underline bar
│  one-line subtitle                           │
│                                              │
│  Foundations  5 SKILLS                       │   burgundy Fraunces + gold caps
│  ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐          │   5 cards (burgundy top stroke)
│  │ ❶ icon  │ │ ❷ icon  │  … │                │   burgundy/gold italic numeral
│  │ NAME    │ │ NAME    │    │                │   Fraunces card title
│  │ benefit │ │ benefit │    │                │   Nunito body
│  └────┘ └────┘ └────┘ └────┘ └────┘          │
│                                              │
│  Power Moves  5 SKILLS                       │
│  (same shape — 6-10 numbered cards total)    │
│                                              │
│  ┌──────────────────────────────────────┐    │
│  │ FIND MORE → github.com/...            │    │   burgundy-bordered strip
│  └──────────────────────────────────────┘    │
│  ─────────────────────────────────────────   │   rule line
│  Week of …   (italic)         @HANDLE        │   footer: italic Fraunces + caps burgundy
└──────────────────────────────────────────────┘
```

## How to make a new weekly infographic

1. Open [../infographic.py](../infographic.py), copy `EMPTY_PRESET`.
2. Fill in title, subtitle, 10 skills (2 sections × 5 each) with short
   benefit-oriented descriptions (under 10 words).
3. Pick emoji icons (one per skill) — keep it clean, 1–2 emojis max.
4. Set `github_link` to the real repo.
5. Render:

   ```python
   from pathlib import Path
   from content_hub.render.infographic import render_infographic, MY_PRESET
   render_infographic(MY_PRESET, Path("/path/to/out"), slug="my-topic")
   ```

Output: `my-topic.png` + `my-topic.pdf`.

## Don'ts

- Don't change palette, fonts, or card count per section.
- Don't add a 3rd section — exactly 2 × 5.
- Don't put more than ~10 words in a card's `desc` — it'll overflow.
- Don't remove the GitHub strip or footer — brand chrome is load-bearing.
- Don't re-introduce Archivo Black / Inter (replaced by Fraunces / Nunito).

---

See [BRAND.md](BRAND.md) for the template set that shares this palette
(carousel, infographic, YouTube talking deck).
