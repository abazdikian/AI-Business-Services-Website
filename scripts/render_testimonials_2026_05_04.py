"""
Render 5 testimonial / real-owner carousels in the editorial template
(white bg, near-black ink, gold mark + gold quote rule, burgundy CTA slide).

Outputs:
  - content_hub/output/{tiktok,instagram}/<slug>/slide-NN.png + carousel.mp4
  - content_hub/drafts/2026-05-04/{tiktok,instagram}/<slug>/post.md (archive)
  - content_hub/output/.../poster-quote.png  (= slide-03.png, single-slide poster)

Configurable per-slide eyebrow (e.g. "PROFILE", "IN THEIR WORDS").

Usage:
    content_hub/venv/bin/python scripts/render_testimonials_2026_05_04.py [--only <slug>] [--no-upload]
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from content_hub.render.carousel import render_carousel
from content_hub.render.video import build_slideshow_mp4
from content_hub.notify.google import drive_service
from content_hub.notify.drive import upload_file, _find_or_create_folder

WEEK = "2026-05-04"
DRAFTS = ROOT / "content_hub" / "drafts" / WEEK
OUT_BASE = ROOT / "content_hub" / "output"

# Drive parents (from prior session)
TIKTOK_PARENT = "1upbi80P9DMa6l9vtB707l-bJmvEGsoDQ"
INSTAGRAM_PARENT = "1ehfOI90p8nT6cbNsvb-2XPXTv58M0AHC"


# ── Carousels ─────────────────────────────────────────────────────────────

CAROUSELS: list[dict] = [
  {
    "slug": "priya-sharma-wellness-coach-testimonial",
    "headline": "What \"useful in so many ways\" really means: a wellness coach's first AI session",
    "slides": [
      {
        "eyebrow": "PROFILE",
        "title": "She runs a wellness practice. Hadn't touched AI before this session.",
        "body": (
          "The pattern most new-to-AI owners arrive with:\n"
          "\n"
          "→ \"It's for tech bros.\"\n"
          "→ \"It's overwhelming.\"\n"
          "→ \"It'll replace what makes me, me.\"\n"
          "\n"
          "Watch what one good session changes."
        ),
      },
      {
        "eyebrow": "THE SETUP",
        "title": "Most \"AI for small business\" content fails new-to-AI owners",
        "body": (
          "Most content assumes you already have an AI stack. You don't.\n"
          "\n"
          "You have a calendar, a Notes app full of intake notes, and a brain holding all your client context. That is the actual stack.\n"
          "\n"
          "The job isn't to add tools. It's to make the stack you already use 2x faster."
        ),
      },
      {
        "eyebrow": "IN HER WORDS",
        "title": "After the AI Fundamentals Session.",
        "body": (
          "\"Please pass on my thanks to Alice. It was a great session. Very useful in so many ways.\"\n"
          "— Priya Sharma, Wellness Coach"
        ),
      },
      {
        "eyebrow": "WHAT THAT MEANT",
        "title": "What \"useful in so many ways\" looks like in week one",
        "body": (
          "→ Intake notes condensed into a one-page client snapshot\n"
          "→ Session recap emails drafted in her voice\n"
          "→ A content calendar that doesn't sound like a wellness chatbot\n"
          "→ Scheduling templates that match how her practice actually books\n"
          "\n"
          "Not 50 tools. Four sharper workflows."
        ),
      },
      {
        "eyebrow": "YOUR MOVE",
        "title": "Want the same starting set for your business?",
        "body": (
          "Free 90-min workshop. Wed June 3 at 7 PM ET. The 4-Workflow AI Stack installed live on a real attendee's small business. 50 seats.\n"
          "\n"
          "Pro tip. Always add to your prompts:\n"
          "\n"
          "\"Ask me clarifying questions until you are 95% confident you can complete the task successfully.\"\n"
          "\n"
          "DM me FUNDAMENTALS, comes back same day"
        ),
      },
    ],
  },
  {
    "slug": "david-chen-operations-testimonial",
    "headline": "He runs ops. Came in skeptical. Left building.",
    "slides": [
      {
        "eyebrow": "PROFILE",
        "title": "He runs ops. Came in skeptical. Left building.",
        "body": (
          "Why ops people are the hardest sell on AI:\n"
          "\n"
          "→ Burned by \"process tools\" that didn't deliver\n"
          "→ Trained to spot the gap between demo and reality\n"
          "→ Allergic to anything that looks like extra work disguised as efficiency"
        ),
      },
      {
        "eyebrow": "THE SETUP",
        "title": "What changes a skeptical ops mind: the right method, not the right pitch",
        "body": (
          "Tutorial overload doesn't move ops people. Neither does hype.\n"
          "\n"
          "What works is structured questioning. Walk them through their actual week, ask what's mechanical vs. what's judgment, then show where AI replaces the mechanical part.\n"
          "\n"
          "Not \"watch me do this.\" \"Show me your process and let's find the leverage.\""
        ),
      },
      {
        "eyebrow": "IN HIS WORDS",
        "title": "After the AI Fundamentals Session.",
        "body": (
          "\"Alice was very good at helping attendees gain an understanding with questions.\"\n"
          "— David Chen, Operations Manager"
        ),
      },
      {
        "eyebrow": "THE METHOD",
        "title": "Teach by asking. Not by demoing.",
        "body": (
          "→ Question 1: Where in your week do you do the same thing more than 3 times?\n"
          "→ Question 2: Which of those tasks is mechanical vs. judgment?\n"
          "→ Question 3: What would change if the mechanical part took 90% less time?\n"
          "\n"
          "Three questions. A real install plan. No demos required."
        ),
      },
      {
        "eyebrow": "YOUR MOVE",
        "title": "Bring your skepticism. Bring your week. We'll do the audit live.",
        "body": (
          "Free 90-min workshop. Wed June 3 at 7 PM ET. Q&A is the centerpiece, not a footer.\n"
          "\n"
          "Pro tip. Always add to your prompts:\n"
          "\n"
          "\"Ask me clarifying questions until you are 95% confident you can complete the task successfully.\"\n"
          "\n"
          "DM me SKEPTIC, comes back same day"
        ),
      },
    ],
  },
  {
    "slug": "rachel-thompson-marketing-testimonial",
    "headline": "She'd tried 12 AI tools. None of them stuck.",
    "slides": [
      {
        "eyebrow": "PROFILE",
        "title": "She'd tried 12 AI tools. None of them stuck.",
        "body": (
          "The tool-of-the-week trap, in one sentence:\n"
          "\n"
          "Saved 47 prompts. Ran 2.\n"
          "\n"
          "Most marketers I audit aren't behind on AI. They're drowning in it."
        ),
      },
      {
        "eyebrow": "THE SETUP",
        "title": "Why tool-stacking fails. Why strategy compounds.",
        "body": (
          "A tool teaches you a feature. A strategy teaches you a system.\n"
          "\n"
          "Features age. Tools get acquired and shut down. Pricing flips.\n"
          "\n"
          "Systems compound. The 4-Workflow Stack you set up this week still works in 12 months, even if half the tools change."
        ),
      },
      {
        "eyebrow": "IN HER WORDS",
        "title": "After the AI for Business Teams session.",
        "body": (
          "\"The different strategies the facilitator offered to use AI and get the maximum results to support business activities.\"\n"
          "— Rachel Thompson, Marketing Consultant"
        ),
      },
      {
        "eyebrow": "THE STACK",
        "title": "Four workflows. One brain. Compounding leverage.",
        "body": (
          "→ Inbox Triage drafts your replies in your voice\n"
          "→ Knowledge Base teaches Claude your business once\n"
          "→ Weekly Marketing Loop turns 90 minutes into a content week\n"
          "→ Invoice Extraction does AP in minutes, not hours\n"
          "\n"
          "Set up once. Compounds forever."
        ),
      },
      {
        "eyebrow": "YOUR MOVE",
        "title": "Stop collecting tools. Install the stack.",
        "body": (
          "Free 90-min workshop. Wed June 3 at 7 PM ET. We install the full 4-Workflow Stack live on a real attendee's small business.\n"
          "\n"
          "Pro tip. Always add to your prompts:\n"
          "\n"
          "\"Ask me clarifying questions until you are 95% confident you can complete the task successfully.\"\n"
          "\n"
          "DM me STACK, comes back same day"
        ),
      },
    ],
  },
  {
    "slug": "real-owners-fragmentation-pain",
    "headline": "What a real small business owner just posted online",
    "slides": [
      {
        "eyebrow": "REAL OWNER",
        "title": "What a real small business owner just posted online",
        "body": (
          "It's not the tools that are bad.\n"
          "\n"
          "Most owners have plenty of good ones. The problem is the way the tools get pieced together.\n"
          "\n"
          "Domain here. Hosting there. Email somewhere else. Website builder over there. None of it talks. All of it breaks at once."
        ),
      },
      {
        "eyebrow": "THE SETUP",
        "title": "The fragmentation tax: 5 tools, no one to call when something breaks",
        "body": (
          "→ Email goes down. Whose problem is it?\n"
          "→ Site stops loading. Which vendor owns the fix?\n"
          "→ Booking link 404s the day before a launch. Three support queues, three days of waiting.\n"
          "\n"
          "It's not the tools. It's the seams between them."
        ),
      },
      {
        "eyebrow": "IN HIS WORDS",
        "title": "From a small business sub.",
        "body": (
          "\"It makes me wonder if the problem isn't the tools, but how fragmented the setup usually is.\"\n"
          "— Real small business owner"
        ),
      },
      {
        "eyebrow": "THE REFRAME",
        "title": "AI consolidates. The 4-Workflow Stack is one tool, not five.",
        "body": (
          "The owners winning right now aren't using more tools. They're using fewer.\n"
          "\n"
          "→ One Knowledge Base project that knows your business\n"
          "→ One inbox triage prompt\n"
          "→ One marketing loop\n"
          "→ One invoice extraction flow\n"
          "\n"
          "All inside Claude Pro. $20 a month. One thing to call when it breaks."
        ),
      },
      {
        "eyebrow": "YOUR MOVE",
        "title": "Stop adding seams. Start consolidating.",
        "body": (
          "Free 90-min workshop. Wed June 3 at 7 PM ET. We install the full consolidated stack live on a real attendee's small business. 50 seats.\n"
          "\n"
          "Pro tip. Always add to your prompts:\n"
          "\n"
          "\"Ask me clarifying questions until you are 95% confident you can complete the task successfully.\"\n"
          "\n"
          "DM me CONNECT, comes back same day"
        ),
      },
    ],
  },
  {
    "slug": "real-owners-vitamins-vs-painkillers",
    "headline": "Why most AI side-projects die in 4 months",
    "slides": [
      {
        "eyebrow": "REAL OWNER",
        "title": "Why most AI side-projects die in 4 months. A real founder's confession.",
        "body": (
          "A lot of owners are spinning up AI side-projects right now. Most quietly die.\n"
          "\n"
          "Here's the line every owner who ships should tape to their monitor before they start anything new."
        ),
      },
      {
        "eyebrow": "THE SETUP",
        "title": "Most AI experiments are vitamins, not painkillers",
        "body": (
          "Vitamins are nice. People know they should take them. They forget.\n"
          "\n"
          "Painkillers are something different. People search for them. People pay for them. People remember the moment the pain stopped.\n"
          "\n"
          "If your new AI project is a vitamin, it dies in 4 months."
        ),
      },
      {
        "eyebrow": "IN HIS WORDS",
        "title": "From an entrepreneur sub.",
        "body": (
          "\"They were vitamins, not painkillers. People thought they were interesting, but nobody was desperately looking for them.\"\n"
          "— Real founder"
        ),
      },
      {
        "eyebrow": "THE FILTER",
        "title": "The painkiller test: 3 questions before you build anything new",
        "body": (
          "→ Is this pain my customer is feeling RIGHT NOW (not next quarter)?\n"
          "→ Are they already paying someone or wasting hours trying to solve it?\n"
          "→ Will they describe my solution in words their boss will understand?\n"
          "\n"
          "Three yeses or it's a vitamin. Build something else."
        ),
      },
      {
        "eyebrow": "YOUR MOVE",
        "title": "Stop building vitamins. Install the painkiller stack.",
        "body": (
          "Free 90-min workshop. Wed June 3 at 7 PM ET. We install three painkiller workflows live on a real attendee's small business: inbox triage, marketing loop, invoice extraction. 50 seats.\n"
          "\n"
          "Pro tip. Always add to your prompts:\n"
          "\n"
          "\"Ask me clarifying questions until you are 95% confident you can complete the task successfully.\"\n"
          "\n"
          "DM me PAINKILLER, comes back same day"
        ),
      },
    ],
  },
]


# ── Helpers ──────────────────────────────────────────────────────────────

def write_post_md(channel: str, slug: str, headline: str, slides: list[dict]) -> Path:
    folder = DRAFTS / channel / slug
    folder.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# {headline}",
        "",
        f"**Channel:** {channel} (carousel, editorial template)",
        f"**Slides:** {len(slides)}",
        "**Pillar:** Testimonials",
        "**Generated:** 2026-05-07",
        "",
        "---",
        "",
    ]
    for i, s in enumerate(slides, 1):
        lines.append(f"## Slide {i} — {s['title']}")
        lines.append("")
        lines.append(s["body"])
        lines.append("")
    p = folder / "post.md"
    p.write_text("\n".join(lines), encoding="utf-8")
    return p


def render_one(channel: str, aspect: str, slug: str, slides: list[dict]) -> tuple[Path, list[Path]]:
    out = OUT_BASE / channel / slug
    out.mkdir(parents=True, exist_ok=True)
    pngs = render_carousel(
        slides,
        out,
        aspect=aspect,
        filename_prefix="slide",
        cover_seed=slug,
        body_size_boost=True,
        template="editorial",
    )
    mp4 = out / "carousel.mp4"
    build_slideshow_mp4(pngs, mp4)
    # Single-slide poster = slide 3 (the quote slide)
    if len(pngs) >= 3:
        shutil.copyfile(pngs[2], out / "poster-quote.png")
    return mp4, pngs


def upload_pillar(channel: str, parent_id: str, slug: str, mp4: Path, pngs: list[Path]):
    svc = drive_service()
    folder_id = _find_or_create_folder(svc, slug, parent_id)
    # Trash any stale files
    q = f"'{folder_id}' in parents and trashed=false"
    for h in svc.files().list(q=q, fields="files(id,name)").execute().get("files", []):
        if h["name"] in ("carousel.mp4", "poster-quote.png") or h["name"].startswith("slide-"):
            svc.files().update(fileId=h["id"], body={"trashed": True}).execute()
    # Upload fresh
    upload_file(mp4, folder_id, mimetype="video/mp4")
    upload_file(mp4.parent / "poster-quote.png", folder_id, mimetype="image/png")
    for p in pngs:
        upload_file(p, folder_id, mimetype="image/png")
    return f"https://drive.google.com/drive/folders/{folder_id}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="Render just this slug")
    ap.add_argument("--no-upload", action="store_true", help="Skip Drive upload")
    args = ap.parse_args()

    targets = [c for c in CAROUSELS if (not args.only or c["slug"] == args.only)]
    if not targets:
        print(f"No carousel matches --only={args.only}")
        sys.exit(1)

    for c in targets:
        slug = c["slug"]
        print(f"\n=== {slug} ===")
        for channel in ("tiktok", "instagram"):
            write_post_md(channel, slug, c["headline"], c["slides"])
        for channel, aspect, parent in (
            ("tiktok", "9:16", TIKTOK_PARENT),
            ("instagram", "4:5", INSTAGRAM_PARENT),
        ):
            print(f"  → {channel} ({aspect})")
            mp4, pngs = render_one(channel, aspect, slug, c["slides"])
            print(f"    {len(pngs)} slides + MP4 ({mp4.stat().st_size//1024} KB)")
            # mirror to drafts folder for review
            draft_dir = DRAFTS / channel / slug
            for asset in [mp4, mp4.parent / "poster-quote.png"] + list(pngs):
                if asset.exists():
                    (draft_dir / asset.name).write_bytes(asset.read_bytes())
            if not args.no_upload:
                url = upload_pillar(channel, parent, slug, mp4, pngs)
                print(f"    uploaded → {url}")

    print("\nDone.")


if __name__ == "__main__":
    main()
