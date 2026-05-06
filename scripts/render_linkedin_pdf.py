"""
Render "The Claude automations that actually make money" as a LinkedIn PDF carousel.
Outputs 6 PNG slides → PDF → uploads to Drive.

Usage:
    content_hub/venv/bin/python scripts/render_linkedin_pdf.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from content_hub.render.carousel import render_carousel
from content_hub.render.pdf import build_carousel_pdf
from content_hub.notify.drive import upload_file

DRIVE_FOLDER_ID = "1-MB15mUWWxaxIbj2YTUK83EvXcVKhG9i"
SLUG = "most-ai-automations-dont-make-money"
OUT_DIR = ROOT / "content_hub" / "output" / "linkedin" / SLUG

SLIDES = [
    {
        "title": "The Claude automations that actually make money",
        "body": (
            "Most solopreneurs spend months building automations nobody asked for.\n"
            "\n"
            "They look great in demos. They get abandoned in weeks.\n"
            "\n"
            "Here's what actually sticks — and why. 👇"
        ),
    },
    {
        "title": "Cool automations nobody actually uses",
        "body": (
            "→ Automated motivational quote senders\n"
            "→ Dashboard reports no one opens\n"
            "→ Workflows that require 3 new tools to maintain\n"
            "→ AI that drafts things — but you still rebuild them from scratch\n"
            "\n"
            "\"So basically you're saying my 'automated motivational quote sender' isn't gonna pay the bills? Shocking.\"\n"
            "— u/Gabby_N_The_Whip\n"
            "\n"
            "The automations that get abandoned share one thing: they don't solve something already painful."
        ),
    },
    {
        "title": "The automations that actually stuck",
        "body": (
            "The ones that worked solved something painful happening every single day.\n"
            "\n"
            "→ Email assistant that drafts replies in the founder's exact tone — inbox time cut from 90 min to 15\n"
            "→ Cold outreach pulling from Google Sheets + website enrichment — 20–30 personalized emails/day\n"
            "→ Sales pipeline validating leads via Apollo + Hunter, writes emails, auto-stops if costs spike\n"
            "→ Lead routing for a real estate team — assigns by agent load, generates talking points instantly\n"
            "\n"
            "Notice what these have in common: daily, painful, and already in the workflow."
        ),
    },
    {
        "title": "The hardest lesson nobody warns you about",
        "body": (
            "\"The AI part is usually the easy bit — but reliability is the only thing that matters. "
            "Rate limits, retries, fallbacks, alerts. Failures are often silent: bad data, wrong context, invalid emails.\"\n"
            "— Original thread author, r/automation\n"
            "\n"
            "Read that twice.\n"
            "\n"
            "This is why I teach clients to configure Claude as a strategist first — not a builder. "
            "Before you automate anything, know WHAT is worth automating and whether it will hold up when something breaks.\n"
            "\n"
            "Cool demos are free. Reliable systems are what you pay for."
        ),
    },
    {
        "title": "How to know if it's worth building",
        "body": (
            "Run every idea through this filter before you touch a single tool:\n"
            "\n"
            "→ Is it painful and daily? — Worth exploring\n"
            "→ Does it live in your existing stack? — Green light\n"
            "→ Would it break silently? — Build a fallback first\n"
            "→ Does it keep a human in the loop on judgment calls? — Non-negotiable\n"
            "→ Does it tie directly to revenue or hours saved? — If not, stop here\n"
            "\n"
            "The goal isn't to automate everything. It's to automate the right things."
        ),
    },
    {
        "title": "What's the one task eating your day?",
        "body": (
            "Drop it in the comments — I'll tell you if it's worth automating or if Claude can just handle it outright.\n"
            "\n"
            "DM me the word DIAGNOSTIC — I'll send the link"
        ),
    },
]


def main():
    print(f"Rendering {len(SLIDES)} slides → {OUT_DIR}")
    pngs = render_carousel(
        SLIDES,
        OUT_DIR,
        aspect="4:5",
        filename_prefix="slide",
        cover_seed=SLUG,
    )
    print(f"Rendered: {[p.name for p in pngs]}")

    pdf_path = OUT_DIR / "carousel.pdf"
    build_carousel_pdf(pngs, pdf_path)
    print(f"PDF built: {pdf_path} ({pdf_path.stat().st_size:,} bytes)")

    print(f"Uploading to Drive folder {DRIVE_FOLDER_ID}...")
    result = upload_file(pdf_path, DRIVE_FOLDER_ID, mimetype="application/pdf")
    print(f"Uploaded: {result['file_url']}")
    print("\nDone.")


if __name__ == "__main__":
    main()
