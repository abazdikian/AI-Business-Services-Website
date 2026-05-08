"""Google Slides talking deck — Brand Refresh v2.

Layout per deck:
  1. Cover        — burgundy bg · gold-tile "ab" monogram · white Fraunces title
  2. Agenda       — white bg · burgundy-tile monogram · Fraunces title · Nunito body
  3..N. Sections  — white bg · section title + bullets + optional pull-quote
     * Speaker notes = short talking prompt; verbatim transcript → transcript.md
  final: Refs     — white bg · URLs + transcript pointer

Palette: burgundy #7A1530, gold #D4A84A, ink #2B1A1F, white.
Fonts: Fraunces (display/italic accents), Nunito (sans body).
Monogram: native Slides shape with Fraunces italic "ab" (no Drive-hosted PNG).
"""

import logging

from .google import drive_service, slides_service

log = logging.getLogger(__name__)

BODY_BULLET_LIMIT = 6
QUOTE_CHAR_LIMIT = 160

# Brand colors as normalized RGB for Slides API
BRAND_BURGUNDY     = {"red": 0x7A / 255, "green": 0x15 / 255, "blue": 0x30 / 255}
BRAND_BURGUNDY_SOFT = {"red": 0x9B / 255, "green": 0x24 / 255, "blue": 0x40 / 255}
BRAND_GOLD         = {"red": 0xD4 / 255, "green": 0xA8 / 255, "blue": 0x4A / 255}
BRAND_GOLD_WARM    = {"red": 0xE6 / 255, "green": 0xC4 / 255, "blue": 0x72 / 255}
BRAND_GOLD_DEEP    = {"red": 0xA8 / 255, "green": 0x7B / 255, "blue": 0x1F / 255}
BRAND_INK          = {"red": 0x2B / 255, "green": 0x1A / 255, "blue": 0x1F / 255}
BRAND_INK_SOFT     = {"red": 0x6B / 255, "green": 0x5A / 255, "blue": 0x5F / 255}
BRAND_WHITE        = {"red": 1.0, "green": 1.0, "blue": 1.0}

# EMU helpers — 1 inch = 914400 EMU
IN = 914400
PT = 12700

# Slide page: 10" × 5.625" for standard 16:9 Google Slides


# ------------------------------------------------------------------
# request helpers
# ------------------------------------------------------------------

def _insert(eid: str, text: str) -> dict:
    return {"insertText": {"objectId": eid, "text": text}}


def _slide_req(page_id: str, title_id: str, body_id: str, index: int) -> dict:
    return {
        "createSlide": {
            "objectId": page_id,
            "insertionIndex": index,
            "slideLayoutReference": {"predefinedLayout": "TITLE_AND_BODY"},
            "placeholderIdMappings": [
                {"layoutPlaceholder": {"type": "TITLE", "index": 0}, "objectId": title_id},
                {"layoutPlaceholder": {"type": "BODY", "index": 0}, "objectId": body_id},
            ],
        }
    }


def _page_bg(page_id: str, color: dict) -> dict:
    return {
        "updatePageProperties": {
            "objectId": page_id,
            "pageProperties": {
                "pageBackgroundFill": {
                    "solidFill": {"color": {"rgbColor": color}}
                }
            },
            "fields": "pageBackgroundFill.solidFill.color",
        }
    }


def _style_text(eid: str, *, font: str, size_pt: int, color: dict,
                bold: bool = False, italic: bool = False) -> dict:
    return {
        "updateTextStyle": {
            "objectId": eid,
            "textRange": {"type": "ALL"},
            "style": {
                "fontFamily": font,
                "fontSize": {"magnitude": size_pt, "unit": "PT"},
                "foregroundColor": {"opaqueColor": {"rgbColor": color}},
                "bold": bold,
                "italic": italic,
            },
            "fields": "fontFamily,fontSize,foregroundColor,bold,italic",
        }
    }


def _center_align(element_id: str) -> dict:
    return {
        "updateParagraphStyle": {
            "objectId": element_id,
            "textRange": {"type": "ALL"},
            "style": {"alignment": "CENTER"},
            "fields": "alignment",
        }
    }


def _rect(page_id: str, rid: str, *, x_emu: int, y_emu: int,
          w_emu: int, h_emu: int, fill: dict, rounded: bool = False) -> list[dict]:
    shape_type = "ROUND_RECTANGLE" if rounded else "RECTANGLE"
    return [
        {
            "createShape": {
                "objectId": rid,
                "shapeType": shape_type,
                "elementProperties": {
                    "pageObjectId": page_id,
                    "size": {
                        "width": {"magnitude": w_emu, "unit": "EMU"},
                        "height": {"magnitude": h_emu, "unit": "EMU"},
                    },
                    "transform": {
                        "scaleX": 1, "scaleY": 1,
                        "translateX": x_emu, "translateY": y_emu,
                        "unit": "EMU",
                    },
                },
            }
        },
        {
            "updateShapeProperties": {
                "objectId": rid,
                "shapeProperties": {
                    "shapeBackgroundFill": {"solidFill": {"color": {"rgbColor": fill}}},
                    "outline": {"propertyState": "NOT_RENDERED"},
                },
                "fields": "shapeBackgroundFill.solidFill.color,outline.propertyState",
            }
        },
    ]


def _text_box(page_id: str, tb_id: str, *, x_emu: int, y_emu: int,
              w_emu: int, h_emu: int) -> dict:
    return {
        "createShape": {
            "objectId": tb_id,
            "shapeType": "TEXT_BOX",
            "elementProperties": {
                "pageObjectId": page_id,
                "size": {
                    "width": {"magnitude": w_emu, "unit": "EMU"},
                    "height": {"magnitude": h_emu, "unit": "EMU"},
                },
                "transform": {
                    "scaleX": 1, "scaleY": 1,
                    "translateX": x_emu, "translateY": y_emu,
                    "unit": "EMU",
                },
            },
        }
    }


def _vertical_middle(element_id: str) -> dict:
    return {
        "updateShapeProperties": {
            "objectId": element_id,
            "shapeProperties": {"contentAlignment": "MIDDLE"},
            "fields": "contentAlignment",
        }
    }


def _monogram_tile(page_id: str, tile_id: str, *, dark_slide: bool,
                   top_left: bool = False) -> list[dict]:
    """'ab' monogram tile. On burgundy slides it's gold w/ burgundy text;
    on white slides it's burgundy w/ gold text.

    Tile is horizontally wider than tall so the "ab" letters sit side-by-
    side (Google Slides adds internal padding to shape text, so a square
    tile wraps "ab" vertically at the chosen font size).

    Default position: top-right corner. Pass top_left=True for cover.
    """
    tile_bg = BRAND_GOLD if dark_slide else BRAND_BURGUNDY
    letter_color = BRAND_BURGUNDY if dark_slide else BRAND_GOLD
    w = int(1.05 * IN)
    h = int(0.70 * IN)
    y = int(0.3 * IN)
    x = int(0.3 * IN) if top_left else int(8.65 * IN)
    reqs = _rect(
        page_id, tile_id,
        x_emu=x, y_emu=y, w_emu=w, h_emu=h,
        fill=tile_bg, rounded=True,
    )
    reqs.append(_insert(tile_id, "ab"))
    reqs.append(_style_text(
        tile_id, font="Fraunces", size_pt=28,
        color=letter_color, bold=True, italic=True,
    ))
    reqs.append(_center_align(tile_id))
    reqs.append(_vertical_middle(tile_id))
    return reqs


def _footer(page_id: str, week_id: str, *,
            divider_id: str, week_tb: str, handle_tb: str,
            dark_slide: bool) -> list[dict]:
    """Gold divider line + week label (left) + handle (right), bottom of page."""
    divider_color = BRAND_GOLD
    week_color = BRAND_WHITE if dark_slide else BRAND_INK_SOFT
    handle_color = BRAND_GOLD if dark_slide else BRAND_BURGUNDY

    reqs = _rect(
        page_id, divider_id,
        x_emu=int(0.5 * IN), y_emu=int(5.0 * IN),
        w_emu=int(9.0 * IN), h_emu=int(0.025 * IN),
        fill=divider_color,
    )
    # Week (left) — italic Fraunces
    reqs.append(_text_box(
        page_id, week_tb,
        x_emu=int(0.5 * IN), y_emu=int(5.12 * IN),
        w_emu=int(4.0 * IN), h_emu=int(0.35 * IN),
    ))
    reqs.append(_insert(week_tb, f"Week of {week_id}"))
    reqs.append(_style_text(
        week_tb, font="Fraunces", size_pt=11,
        color=week_color, italic=True,
    ))
    # Handle (right) — uppercase Nunito, burgundy/gold
    reqs.append(_text_box(
        page_id, handle_tb,
        x_emu=int(5.5 * IN), y_emu=int(5.12 * IN),
        w_emu=int(4.0 * IN), h_emu=int(0.35 * IN),
    ))
    reqs.append(_insert(handle_tb, "@SMALLBUSINESSAICOACH"))
    reqs.append(_style_text(
        handle_tb, font="Nunito", size_pt=10,
        color=handle_color, bold=True,
    ))
    reqs.append({
        "updateParagraphStyle": {
            "objectId": handle_tb,
            "textRange": {"type": "ALL"},
            "style": {"alignment": "END"},
            "fields": "alignment",
        }
    })
    return reqs


def _find_notes_body_id(slide: dict) -> str | None:
    notes_page = slide.get("slideProperties", {}).get("notesPage")
    if not notes_page:
        return None
    for elt in notes_page.get("pageElements", []):
        ph = (elt.get("shape") or {}).get("placeholder") or {}
        if ph.get("type") == "BODY":
            return elt["objectId"]
    return None


# ------------------------------------------------------------------
# main
# ------------------------------------------------------------------

def build_transcript_deck(
    *,
    video_title: str,
    creator: str,
    video_url: str,
    sections_payload: dict,
    drive_folder_id: str | None = None,
    week_id: str = "",
) -> dict:
    slides = slides_service()
    drive = drive_service()

    deck_title = f"{(video_title or 'YouTube')[:80]} — talking deck"
    pres = slides.presentations().create(body={"title": deck_title}).execute()
    pres_id = pres["presentationId"]
    default_slide = pres["slides"][0]["objectId"]

    sections = sections_payload.get("sections", []) or []
    section_count = len(sections)

    # PASS 1 — structural
    page_ids: list[str] = ["cover", "agenda"]
    for i in range(1, section_count + 1):
        page_ids.append(f"sect_{i}")
    page_ids.append("refs_page")

    struct: list[dict] = [{"deleteObject": {"objectId": default_slide}}]
    # Cover uses BLANK layout — we build the title page manually with
    # centered text boxes so it actually reads like a title slide.
    struct.append({
        "createSlide": {
            "objectId": "cover",
            "insertionIndex": 0,
            "slideLayoutReference": {"predefinedLayout": "BLANK"},
        }
    })
    struct.append(_slide_req("agenda", "agen_t", "agen_b", 1))
    for i in range(1, section_count + 1):
        struct.append(_slide_req(f"sect_{i}", f"sect_{i}_t", f"sect_{i}_b", i + 1))
    struct.append(_slide_req("refs_page", "refs_t", "refs_b", section_count + 2))
    slides.presentations().batchUpdate(
        presentationId=pres_id, body={"requests": struct}
    ).execute()

    # PASS 2 — text + typography
    text_reqs: list[dict] = []

    # Cover (BLANK layout with custom text boxes — real title-page treatment)
    cover_title = (video_title or "YouTube").strip()[:140]
    summary = sections_payload.get("video_summary", "").strip()
    angle = sections_payload.get("her_angle", "").strip()

    # Eyebrow (gold caps, centered) — e.g. "FEATURED VIDEO · 7 SECTIONS"
    eyebrow_text = f"FEATURED VIDEO  ·  {section_count} SECTIONS"
    text_reqs.append(_text_box(
        "cover", "cov_eyebrow",
        x_emu=int(0.5 * IN), y_emu=int(1.35 * IN),
        w_emu=int(9.0 * IN), h_emu=int(0.4 * IN),
    ))
    text_reqs.append(_insert("cov_eyebrow", eyebrow_text))
    text_reqs.append(_style_text(
        "cov_eyebrow", font="Nunito", size_pt=12,
        color=BRAND_GOLD, bold=True,
    ))
    text_reqs.append(_center_align("cov_eyebrow"))

    # Big title — Fraunces serif, white, centered
    text_reqs.append(_text_box(
        "cover", "cov_title",
        x_emu=int(0.5 * IN), y_emu=int(1.85 * IN),
        w_emu=int(9.0 * IN), h_emu=int(1.8 * IN),
    ))
    text_reqs.append(_insert("cov_title", cover_title))
    text_reqs.append(_style_text(
        "cov_title", font="Fraunces", size_pt=40,
        color=BRAND_WHITE, bold=True,
    ))
    text_reqs.append(_center_align("cov_title"))

    # Gold accent bar — short, centered below title area
    text_reqs.extend(_rect(
        "cover", "cov_bar",
        x_emu=int(4.55 * IN), y_emu=int(3.80 * IN),
        w_emu=int(0.9 * IN), h_emu=int(0.05 * IN),
        fill=BRAND_GOLD,
    ))

    # Subtitle — creator + angle below the bar
    sub_lines = []
    if creator:
        sub_lines.append(f"Source · {creator}")
    if angle:
        sub_lines.append("")
        sub_lines.append(angle)
    if not sub_lines and summary:
        sub_lines.append(summary)
    text_reqs.append(_text_box(
        "cover", "cov_sub",
        x_emu=int(1.0 * IN), y_emu=int(4.00 * IN),
        w_emu=int(8.0 * IN), h_emu=int(0.9 * IN),
    ))
    text_reqs.append(_insert("cov_sub", "\n".join(sub_lines) or " "))
    text_reqs.append(_style_text(
        "cov_sub", font="Nunito", size_pt=13,
        color=BRAND_WHITE,
    ))
    text_reqs.append(_center_align("cov_sub"))

    # Agenda (white slide → burgundy title + ink body)
    agenda_lines = [
        f"{i:02d} · {(sec.get('title') or 'Section').strip()[:80]}"
        for i, sec in enumerate(sections, 1)
    ] or [" "]
    text_reqs += [
        _insert("agen_t", "Agenda"),
        _style_text("agen_t", font="Fraunces", size_pt=34,
                    color=BRAND_BURGUNDY, bold=True),
        _insert("agen_b", "\n".join(agenda_lines)),
        _style_text("agen_b", font="Nunito", size_pt=16, color=BRAND_INK),
    ]

    # Sections (white slides)
    for i, sec in enumerate(sections, 1):
        title = (sec.get("title") or f"Section {i}").strip()[:100]
        bullets = [b.strip() for b in (sec.get("bullets") or []) if b.strip()][:BODY_BULLET_LIMIT]
        quote = (sec.get("quote") or "").strip()
        body_lines = [f"• {b}" for b in bullets] or [" "]
        if quote:
            body_lines.append("")
            body_lines.append(f"\u201c{quote[:QUOTE_CHAR_LIMIT]}\u201d")
        text_reqs += [
            _insert(f"sect_{i}_t", title),
            _style_text(f"sect_{i}_t", font="Fraunces", size_pt=26,
                        color=BRAND_BURGUNDY, bold=True),
            _insert(f"sect_{i}_b", "\n".join(body_lines)),
            _style_text(f"sect_{i}_b", font="Nunito", size_pt=14, color=BRAND_INK),
        ]

    # Refs (white slide)
    refs_body = (
        f"Watch: {video_url}\n"
        f"Creator: {creator or 'n/a'}\n\n"
        f"Full transcript: transcript.md in the Drive folder"
    )
    text_reqs += [
        _insert("refs_t", "References"),
        _style_text("refs_t", font="Fraunces", size_pt=34,
                    color=BRAND_BURGUNDY, bold=True),
        _insert("refs_b", refs_body),
        _style_text("refs_b", font="Nunito", size_pt=13, color=BRAND_INK),
    ]

    slides.presentations().batchUpdate(
        presentationId=pres_id, body={"requests": text_reqs}
    ).execute()

    # PASS 3 — chrome: bg, monogram, center-align titles, footer
    chrome: list[dict] = []
    # Interior slides use placeholders; cover is custom text boxes (handled in pass 2)
    title_ids = {"agenda": "agen_t", "refs_page": "refs_t"}
    for i in range(1, section_count + 1):
        title_ids[f"sect_{i}"] = f"sect_{i}_t"

    for pid in page_ids:
        dark = (pid == "cover")
        chrome.append(_page_bg(pid, BRAND_BURGUNDY if dark else BRAND_WHITE))
        # On the cover, anchor the monogram top-LEFT so it doesn't fight the
        # centered title block. On interior slides, keep it top-right.
        chrome.extend(_monogram_tile(
            pid, f"{pid}_mono", dark_slide=dark, top_left=dark,
        ))
        chrome.extend(_footer(
            pid, week_id,
            divider_id=f"{pid}_div",
            week_tb=f"{pid}_wk",
            handle_tb=f"{pid}_handle",
            dark_slide=dark,
        ))
        if pid in title_ids:
            chrome.append(_center_align(title_ids[pid]))

    slides.presentations().batchUpdate(
        presentationId=pres_id, body={"requests": chrome}
    ).execute()

    # PASS 4 — speaker notes (talking prompts per section)
    pres_full = slides.presentations().get(presentationId=pres_id).execute()
    notes_reqs: list[dict] = []
    for slide in pres_full["slides"]:
        pid = slide["objectId"]
        if not pid.startswith("sect_"):
            continue
        try:
            idx = int(pid[len("sect_"):]) - 1
        except ValueError:
            continue
        if idx >= len(sections):
            continue
        notes_id = _find_notes_body_id(slide)
        if not notes_id:
            continue
        sec = sections[idx]
        lines = [f"Section: {sec.get('title', '')}"]
        if sec.get("quote"):
            lines.append("")
            lines.append(f"Pull-quote: {sec['quote']}")
        lines.append("")
        lines.append("Open transcript.md in the same Drive folder for the verbatim source.")
        notes_reqs.append(_insert(notes_id, "\n".join(lines)))
    if notes_reqs:
        slides.presentations().batchUpdate(
            presentationId=pres_id, body={"requests": notes_reqs}
        ).execute()

    # Move to Drive folder
    if drive_folder_id:
        f = drive.files().get(fileId=pres_id, fields="parents").execute()
        prev = ",".join(f.get("parents", [])) or ""
        drive.files().update(
            fileId=pres_id,
            addParents=drive_folder_id,
            removeParents=prev,
            fields="id, parents",
        ).execute()

    url = f"https://docs.google.com/presentation/d/{pres_id}/edit"
    log.info("Deck created: %s (%d sections)", url, section_count)
    return {
        "presentation_id": pres_id,
        "slides_url": url,
        "section_count": section_count,
    }
