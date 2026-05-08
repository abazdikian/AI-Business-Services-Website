"""Batch-render TikTok (9:16) + Instagram (4:5) carousel MP4s + slide PNGs
for the 2026-05-04 pillars, then upload to per-pillar Drive folders.

Standing rules baked in:
  - TT/IG body uses body_size_boost=True (mobile legibility, body-large mod)
  - TT aspect 9:16, IG aspect 4:5
  - Each pillar gets carousel.mp4 + slide-NN.png in its Drive folder

Usage:
    content_hub/venv/bin/python scripts/render_ttig_batch_2026_05_04.py
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from content_hub.render.carousel import render_carousel
from content_hub.render.video import build_slideshow_mp4
from content_hub.notify.google import drive_service
from content_hub.notify.drive import upload_file

WEEK = "2026-05-04"
DRAFTS = ROOT / "content_hub" / "drafts" / WEEK
OUT_BASE = ROOT / "content_hub" / "output"

SLIDE_HEADER_RE = re.compile(r"^## Slide \d+ — (.+)$", re.MULTILINE)


def parse_slides(post_md: str) -> list[dict]:
    parts = SLIDE_HEADER_RE.split(post_md)
    slides = []
    for i in range(1, len(parts), 2):
        title = parts[i].strip()
        body = parts[i + 1].strip() if i + 1 < len(parts) else ""
        slides.append({"title": title, "body": body})
    return slides


# slug -> Drive folder ID, per channel.
TIKTOK = {
    "messy-sops-to-10-hours-saved":             "1S6IYIfgHD4njIhLMRRQDCnG2zcGGeRlM",
    "5-monday-ai-questions-for-small-business": "1BuykIEkZwVXKluKfgFzeSApfayF-Hfxm",
    "ai-questions-when-creating-an-offer":      "1mdvJIHFYG7FXiltxA3FO3xTVq5XSwpV3",
    "easiest-ai-stack-for-small-business":      "1LDgEQvtd8RbViCJ-wqmURS6CuoOny4mg",
    "7-prompts-to-plan-a-marketing-month":      "10T-IwHLNFBBjK4xGvg81sAhjh2zMZamD",
    "ai-as-your-invoice-assistant":             "17abBJDCDb-3bNLiabP6mc_Mx2iZKdssJ",
    "4-weekly-ai-tasks-and-the-one-i-refuse":   "1UWhJRnb3TdFruXJWrR9y7NIFPxMxvE9a",
}
INSTAGRAM = {
    "messy-sops-to-10-hours-saved":             "1GmswI4i-Br0QtwmOE6EKT2nXpa_2vqni",
    "5-monday-ai-questions-for-small-business": "1XvVeBFPVvU_W0W2hZr1CmLhmdyQ9iU2T",
    "easiest-ai-stack-for-small-business":      "14r-6QTwO41gybqnPPMOUNYU4wtNH7ofC",
    "7-prompts-to-plan-a-marketing-month":      "1tmfhK2BnqbTe2SpChnZ87xZKiA3RSHNI",
    "ai-as-your-invoice-assistant":             "1Gjn3wIb_b_31MHcMays_7wNgXyfiWwOh",
}


def render_channel(channel: str, aspect: str, folder_map: dict[str, str]):
    drafts_dir = DRAFTS / channel
    out_dir_base = OUT_BASE / channel
    svc = drive_service()

    print(f"\n{'='*60}\nRendering {channel.upper()} ({aspect}) — {len(folder_map)} pillars\n{'='*60}")

    for slug, drive_folder_id in folder_map.items():
        post_path = drafts_dir / slug / "post.md"
        if not post_path.exists():
            print(f"  SKIP {slug}: no post.md")
            continue

        slides = parse_slides(post_path.read_text(encoding="utf-8"))
        if len(slides) < 3:
            print(f"  FAIL {slug}: only {len(slides)} slides parsed")
            continue

        out_dir = out_dir_base / slug
        out_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n  → {slug} ({len(slides)} slides)")
        pngs = render_carousel(
            slides,
            out_dir,
            aspect=aspect,
            filename_prefix="slide",
            cover_seed=slug,
            body_size_boost=True,
        )
        mp4_path = out_dir / "carousel.mp4"
        build_slideshow_mp4(pngs, mp4_path)
        size_mb = mp4_path.stat().st_size / (1024 * 1024)
        print(f"    MP4 ({size_mb:.1f} MB) + {len(pngs)} PNGs")

        # Mirror to drafts folder so review surfaces match
        for asset in [mp4_path] + list(pngs):
            (drafts_dir / slug / asset.name).write_bytes(asset.read_bytes())

        # Trash any stale carousel.mp4 in Drive, then upload fresh
        q = f"name='carousel.mp4' and '{drive_folder_id}' in parents and trashed=false"
        for h in svc.files().list(q=q, fields="files(id)").execute().get("files", []):
            svc.files().update(fileId=h["id"], body={"trashed": True}).execute()

        # Trash stale slide PNGs too
        q_png = f"name contains 'slide-' and '{drive_folder_id}' in parents and trashed=false and mimeType='image/png'"
        for h in svc.files().list(q=q_png, fields="files(id,name)").execute().get("files", []):
            svc.files().update(fileId=h["id"], body={"trashed": True}).execute()

        res = upload_file(mp4_path, drive_folder_id, mimetype="video/mp4")
        print(f"    uploaded MP4: {res['file_url']}")
        for png in pngs:
            upload_file(png, drive_folder_id, mimetype="image/png")
        print(f"    uploaded {len(pngs)} slide PNGs")


def main():
    render_channel("tiktok", "9:16", TIKTOK)
    # Instagram skipped per user request 2026-05-07
    print("\nDone.")


if __name__ == "__main__":
    main()
