"""One-off: re-draft 3 LinkedIn posts with the new rich-body drafter,
replace Drive files in-place, delete old local .md files.
Run from repo root:
  content_hub/venv/bin/python scripts/redraft_linkedin.py
"""
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

from content_hub.generate.drafter import draft_carousel
from content_hub.generate.voice import load_voice_profile
from content_hub.notify.drive import drive_service, upload_file

CHANNEL = "linkedin"
WEEK_ID = "2026-04-20"

POSTS = [
    {
        "slug": "most-ai-automations-dont-make-money",
        "source_url": "https://www.reddit.com/r/automation/comments/1smvx6v/what_automations_actually_make_money_heres_what/",
        "drive_folder_id": "1-MB15mUWWxaxIbj2YTUK83EvXcVKhG9i",
        "old_post_file_id": "1SlGMbuJQ6CU8FJbBKKtLVGiqVaSGsPlJ",
        "old_caption_file_id": "1vZEfrxSEGHf0JsTTgPJJ-xhOnI8ZgMM_",
        "local_dir": "content_hub/drafts/2026-04-20/linkedin/most-ai-automations-dont-make-money",
    },
    {
        "slug": "small-business-owners-dont-have-an-ai-problem",
        "source_url": "https://www.reddit.com/r/AIforOPS/comments/1somg6s/spent_time_talking_to_small_business_owners_about/",
        "drive_folder_id": "1gmu7mJsFDTwwSC6z-opSdlgcwu4eRX62",
        "old_post_file_id": "1yyVf9Wdl9yMn01Q_R_8HxgGIDjdKQiXM",
        "old_caption_file_id": "1d8Y6OSarjfHYyA6pW9Ae7qh5wiNv3aac",
        "local_dir": "content_hub/drafts/2026-04-20/linkedin/small-business-owners-dont-have-an-ai-problem",
    },
    {
        "slug": "claude-isnt-a-chatbot-its-your-strategist",
        "source_url": "https://www.reddit.com/r/ClaudeAI/comments/1sad9rb/how_are_people_using_claude_as_a_personal/",
        "drive_folder_id": "184wxwc805LbwRnDX1b2NzLMFJDHZB-_B",
        "old_post_file_id": "1bv-MQMjXwwE20ZZigaFHOdNxHkRVfzfd",
        "old_caption_file_id": "1Iig97WmF2gJwoawXXqI9c9Z9e5OLLy0A",
        "local_dir": "content_hub/drafts/2026-04-20/linkedin/claude-isnt-a-chatbot-its-your-strategist",
    },
]


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _carousel_post_md(*, hook: str, channel: str, slides: list, caption: str,
                      source_url: str) -> str:
    lines = [
        f"# {hook}",
        "",
        f"**Channel:** {channel} (carousel)",
        f"**Slides:** {len(slides)}",
        f"**Source:** {source_url}",
        f"**Generated:** {_now_utc()}",
        "",
        "---",
        "",
    ]
    for i, s in enumerate(slides, 1):
        lines.append(f"## Slide {i} — {s.get('title', '').strip()}")
        body = (s.get("body") or "").strip()
        if body:
            lines.append("")
            lines.append(body)
        lines.append("")
    return "\n".join(lines)


def _caption_md(*, hook: str, channel: str, source_url: str, caption: str) -> str:
    lines = [
        f"# {hook}",
        "",
        f"**Channel:** {channel} (feed caption)",
        f"**Source:** {source_url}",
        f"**Generated:** {_now_utc()}",
        "",
        "---",
        "",
        caption.strip(),
        "",
    ]
    return "\n".join(lines)


def _trash_file(svc, file_id: str) -> None:
    try:
        svc.files().update(fileId=file_id, body={"trashed": True}).execute()
        log.info("Trashed Drive file %s", file_id)
    except Exception as e:
        log.warning("Could not trash %s: %s", file_id, e)


def main():
    voice_profile = load_voice_profile()
    if not voice_profile:
        log.error("No voice profile found")
        sys.exit(1)

    svc = drive_service()
    results = []

    for p in POSTS:
        log.info("=== Drafting: %s ===", p["slug"])
        stub = {
            "creator_handle": "Reddit thread",
            "caption": "",
            "hook_line": "",
            "format_tag": "discussion thread",
            "why_trending": "Real small business owners sharing AI use cases",
            "post_url": p["source_url"],
        }

        from content_hub.generate.drafter import _fetch_reddit_post, draft_carousel
        reddit = _fetch_reddit_post(p["source_url"])
        if reddit:
            parts = []
            if reddit.get("body"):
                parts.append(reddit["body"])
            if reddit.get("comments"):
                parts.append("--- TOP COMMENTS ---\n" + reddit["comments"])
            stub["caption"] = "\n\n".join(parts)
            stub["hook_line"] = reddit.get("title", "")

        out = draft_carousel(CHANNEL, stub, voice_profile)
        slides = out.get("slides", [])
        caption = out.get("caption", "")

        if not slides:
            log.error("No slides returned for %s — skipping", p["slug"])
            results.append({"slug": p["slug"], "status": "ERROR: no slides"})
            continue

        hook = slides[0].get("title", p["slug"])
        local_dir = Path(p["local_dir"])
        local_dir.mkdir(parents=True, exist_ok=True)

        post_path = local_dir / "post.md"
        caption_path = local_dir / "caption.md"

        post_path.write_text(_carousel_post_md(
            hook=hook, channel=CHANNEL, slides=slides,
            caption=caption, source_url=p["source_url"],
        ))
        caption_path.write_text(_caption_md(
            hook=hook, channel=CHANNEL, source_url=p["source_url"], caption=caption,
        ))
        log.info("Wrote local files: %s", local_dir)

        # Trash old Drive files
        _trash_file(svc, p["old_post_file_id"])
        _trash_file(svc, p["old_caption_file_id"])

        # Upload new files
        post_up = upload_file(post_path, p["drive_folder_id"])
        caption_up = upload_file(caption_path, p["drive_folder_id"])

        results.append({
            "slug": p["slug"],
            "hook": hook,
            "slides": len(slides),
            "drive_folder": f"https://drive.google.com/drive/folders/{p['drive_folder_id']}",
            "post_url": post_up.get("file_url"),
            "caption_url": caption_up.get("file_url"),
            "status": "OK",
        })
        log.info("Done: %s — %d slides uploaded", p["slug"], len(slides))

    print("\n=== RESULTS ===")
    for r in results:
        print(f"\n{r['slug']} [{r.get('status')}]")
        if r.get("hook"):
            print(f"  Hook: {r['hook']}")
            print(f"  Slides: {r['slides']}")
            print(f"  Folder: {r['drive_folder']}")


if __name__ == "__main__":
    main()
