"""Create-batch worker: selected posts → Alice-voice drafts + (for YouTube)
transcript + talking deck. Files are named by hook/title slug, mirrored to
Drive, and Alice gets one approval email per batch.

Run:  python -m content_hub.jobs.create_worker
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path

from .. import db
from ..config import BASE_DIR
from ..generate.deck_sections import summarize_transcript
from ..generate.drafter import draft_carousel, draft_post
from ..generate.naming import ensure_unique, hook_line, slugify, video_title_from_caption
from ..generate.transcript import fetch_transcript
from ..generate.voice import load_voice_profile
from ..notify.drive import channel_folder, upload_file, video_folder
from ..notify.email import send_drafts_email
from ..notify.slides import build_transcript_deck
from ..render.carousel import CHANNEL_SIZE, render_carousel
from ..render.pdf import build_carousel_pdf
from ..render.video import build_slideshow_mp4

log = logging.getLogger(__name__)
POLL_INTERVAL_SECS = 5
DRAFTS_DIR = BASE_DIR / "drafts"


def _now_utc() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


# ------------------------------------------------------------------
# markdown builders
# ------------------------------------------------------------------

def _carousel_post_md(*, hook: str, channel: str, creator: str | None,
                      source_url: str | None, slides: list[dict]) -> str:
    lines = [
        f"# {hook}",
        "",
        f"**Channel:** {channel} (carousel)",
        f"**Slides:** {len(slides)}",
    ]
    if creator:
        lines.append(f"**Inspired by:** @{creator}")
    if source_url:
        lines.append(f"**Source:** {source_url}")
    lines.append(f"**Generated:** {_now_utc()}")
    lines.append("")
    lines.append("---")
    lines.append("")
    for i, s in enumerate(slides, 1):
        lines.append(f"## Slide {i} — {s.get('title', '').strip()}")
        sub = (s.get("sub_line") or s.get("body") or "").strip()
        if sub:
            lines.append("")
            lines.append(sub)
        lines.append("")
    return "\n".join(lines)


def _caption_md(*, hook: str, channel: str, creator: str | None,
                source_url: str | None, caption: str) -> str:
    lines = [
        f"# {hook}",
        "",
        f"**Channel:** {channel} (feed caption)",
    ]
    if creator:
        lines.append(f"**Inspired by:** @{creator}")
    if source_url:
        lines.append(f"**Source:** {source_url}")
    lines.append(f"**Generated:** {_now_utc()}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(caption.strip())
    lines.append("")
    return "\n".join(lines)


def _transcript_md(video_title: str, creator: str, video_url: str, transcript: dict) -> str:
    lines = [
        f"# {video_title} — transcript",
        "",
        f"**Creator:** @{creator}" if creator else "",
        f"**URL:** {video_url}",
        f"**Language:** {transcript.get('language', 'en')}",
        f"**Length:** {len(transcript.get('text', ''))} characters",
        f"**Fetched:** {_now_utc()}",
        "",
        "---",
        "",
        transcript.get("text", "").strip(),
        "",
    ]
    return "\n".join(l for l in lines if l is not None)


def _description_md(draft: dict, video_title: str, video_url: str, creator: str) -> str:
    lines = [
        f"# {hook_line(draft.get('draft') or '') or video_title}",
        "",
        "**Channel:** YouTube description",
        f"**For video:** {video_title}",
        f"**Video URL:** {video_url}",
    ]
    if creator:
        lines.append(f"**Inspired by:** @{creator}")
    lines.append(f"**Generated:** {_now_utc()}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append((draft.get("draft") or "").strip())
    lines.append("")
    return "\n".join(lines)


# ------------------------------------------------------------------
# non-YouTube path
# ------------------------------------------------------------------

def _handle_social(week_id: str, channel: str, posts: list[dict],
                   pasted_urls: list[str], voice_profile: str) -> dict:
    """Each selected post → per-post folder {post.md, caption.md}, named by hook slug."""
    chan_dir = DRAFTS_DIR / week_id / channel
    chan_dir.mkdir(parents=True, exist_ok=True)

    chan_drive = channel_folder(week_id, channel)

    artifacts: list[dict] = []
    posts_plus_pasted: list[tuple[str, dict]] = [("selected", p) for p in posts]
    for url in pasted_urls:
        posts_plus_pasted.append(("pasted", {
            "creator_handle": "(pasted URL)",
            "caption": f"Source URL: {url}",
            "hook_line": "",
            "format_tag": "unknown",
            "why_trending": "",
            "post_url": url,
            "id": None,
        }))

    for kind, source in posts_plus_pasted:
        try:
            payload = draft_carousel(channel, source, voice_profile)
        except Exception as e:  # noqa: BLE001
            log.exception("carousel draft failed for %s", source.get("id") or source.get("post_url"))
            artifacts.append({
                "kind": "post",
                "title": "draft failed",
                "errors": {"drafter": str(e)},
                "creator": source.get("creator_handle"),
                "source_url": source.get("post_url"),
            })
            continue

        slides = payload.get("slides") or []
        caption = payload.get("caption") or ""
        hook = (slides[0]["title"] if slides and slides[0].get("title") else
                hook_line(caption)) or "untitled"

        base = slugify(hook)
        slug = ensure_unique(lambda s: chan_dir / s, base)
        post_dir = chan_dir / slug
        post_dir.mkdir(parents=True, exist_ok=True)

        post_path = post_dir / "post.md"
        caption_path = post_dir / "caption.md"
        post_path.write_text(_carousel_post_md(
            hook=hook, channel=channel,
            creator=source.get("creator_handle"),
            source_url=source.get("post_url"),
            slides=slides,
        ), encoding="utf-8")
        caption_path.write_text(_caption_md(
            hook=hook, channel=channel,
            creator=source.get("creator_handle"),
            source_url=source.get("post_url"),
            caption=caption,
        ), encoding="utf-8")

        # Upload text drafts to Drive — render happens only after approval
        drive_folder_id = None
        drive_folder_url = None
        post_file_url = None
        caption_file_url = None
        errors: dict = {}
        if chan_drive:
            try:
                pf = video_folder(week_id, channel, slug)
                if pf:
                    drive_folder_id = pf["folder_id"]
                    drive_folder_url = pf["folder_url"]
                    post_file_url = upload_file(post_path, drive_folder_id).get("file_url")
                    caption_file_url = upload_file(caption_path, drive_folder_id).get("file_url")
            except Exception as e:  # noqa: BLE001
                log.exception("drive upload failed for %s", slug)
                errors["drive"] = str(e)

        artifacts.append({
            "kind": "post",
            "title": hook[:120],
            "slug": slug,
            "source_kind": kind,
            "creator": source.get("creator_handle"),
            "source_url": source.get("post_url"),
            "local_folder": str(post_dir.relative_to(BASE_DIR)),
            "drive_folder_id": drive_folder_id,
            "drive_folder_url": drive_folder_url,
            "post_file_url": post_file_url,
            "caption_file_url": caption_file_url,
            "slides_data": slides,
            "slides_count": len(slides),
            "caption_preview": caption[:260],
            "needs_render": True,
            "image_count": 0,
            "image_urls": [],
            "video_file_url": None,
            "pdf_file_url": None,
            "errors": errors,
        })

    return {
        "drafts_count": len(artifacts),
        "artifacts": artifacts,
        "drive_folder_url": chan_drive["folder_url"] if chan_drive else None,
    }


# ------------------------------------------------------------------
# YouTube path
# ------------------------------------------------------------------

def _handle_youtube(week_id: str, posts: list[dict], voice_profile: str) -> dict:
    """For each video: transcript.md + description.md + talking deck, all
    inside a per-video folder named by the video title slug.
    """
    chan_dir = DRAFTS_DIR / week_id / "youtube"
    chan_dir.mkdir(parents=True, exist_ok=True)

    chan_drive = channel_folder(week_id, "youtube")

    artifacts: list[dict] = []
    draft_count = 0

    for post in posts:
        title = video_title_from_caption(post.get("caption") or "") or "Untitled video"
        creator = post.get("creator_handle") or ""
        video_url = post.get("post_url") or ""
        slug = slugify(title)

        video_dir = chan_dir / slug
        video_dir.mkdir(parents=True, exist_ok=True)

        # Drive folder for this video
        video_drive = video_folder(week_id, "youtube", slug) if chan_drive else None
        video_folder_id = video_drive["folder_id"] if video_drive else None

        entry: dict = {
            "kind": "video",
            "title": title,
            "creator": creator,
            "video_url": video_url,
            "slug": slug,
            "local_folder": str(video_dir.relative_to(BASE_DIR)),
            "drive_folder_url": video_drive["folder_url"] if video_drive else None,
            "transcript_file_url": None,
            "description_file_url": None,
            "slides_url": None,
            "section_count": 0,
            "errors": {},
        }

        # 1. Transcript
        try:
            tx = fetch_transcript(video_url)
        except Exception as e:  # noqa: BLE001
            log.exception("transcript fetch exception for %s", video_url)
            tx = None
            entry["errors"]["transcript"] = str(e)

        if not tx:
            entry["errors"].setdefault("transcript", "no transcript available")
        else:
            tx_path = video_dir / "transcript.md"
            tx_path.write_text(_transcript_md(title, creator, video_url, tx), encoding="utf-8")
            if video_folder_id:
                try:
                    up = upload_file(tx_path, video_folder_id)
                    entry["transcript_file_url"] = up.get("file_url")
                except Exception as e:  # noqa: BLE001
                    log.exception("transcript drive upload failed")
                    entry["errors"]["transcript_upload"] = str(e)

        # 2. Description (Alice-voice draft of YT description)
        try:
            draft_body = draft_post("youtube", post, voice_profile)
            draft = {
                "source_kind": "selected",
                "source_id": post.get("id"),
                "source_url": video_url,
                "creator": creator,
                "draft": draft_body,
            }
            draft_count += 1
            desc_path = video_dir / "description.md"
            desc_path.write_text(_description_md(draft, title, video_url, creator), encoding="utf-8")
            if video_folder_id:
                try:
                    up = upload_file(desc_path, video_folder_id)
                    entry["description_file_url"] = up.get("file_url")
                except Exception as e:  # noqa: BLE001
                    log.exception("description drive upload failed")
                    entry["errors"]["description_upload"] = str(e)
        except Exception as e:  # noqa: BLE001
            log.exception("description draft failed")
            entry["errors"]["description"] = str(e)

        # 3. Talking deck (summary + agenda — no transcript verbatim on slides)
        if tx:
            try:
                sections = summarize_transcript(
                    title=title, creator=creator, transcript_text=tx["text"],
                )
                deck = build_transcript_deck(
                    video_title=title,
                    creator=creator,
                    video_url=video_url,
                    sections_payload=sections,
                    drive_folder_id=video_folder_id,
                    week_id=week_id,
                )
                entry["slides_url"] = deck["slides_url"]
                entry["section_count"] = deck["section_count"]
            except Exception as e:  # noqa: BLE001
                log.exception("deck build failed")
                entry["errors"]["deck"] = str(e)
        else:
            entry["errors"].setdefault("deck", "skipped (no transcript)")

        artifacts.append(entry)

    return {
        "drafts_count": draft_count,
        "artifacts": artifacts,
        "drive_folder_url": chan_drive["folder_url"] if chan_drive else None,
    }


# ------------------------------------------------------------------
# entry points
# ------------------------------------------------------------------

def handle(job: dict) -> dict:
    payload = json.loads(job["payload_json"] or "{}")
    post_ids = payload.get("post_ids", [])
    pasted_urls = payload.get("pasted_urls", [])
    channel = job["channel"]
    week_id = job["week_id"]
    log.info(
        "Processing job %s week=%s channel=%s posts=%d pasted=%d",
        job["id"], week_id, channel, len(post_ids), len(pasted_urls),
    )

    if not post_ids and not pasted_urls:
        return {"drafts_count": 0, "note": "no selections or pasted URLs"}

    voice_profile = load_voice_profile()
    if not voice_profile:
        log.warning("voice profile empty — drafts will be low quality")

    posts = db.posts_by_ids(post_ids)

    if channel == "youtube":
        result = _handle_youtube(week_id, posts, voice_profile)
    else:
        result = _handle_social(
            week_id, channel, posts, pasted_urls, voice_profile,
        )

    email_id = None
    email_err = None
    try:
        email_id = send_drafts_email(
            channel=channel,
            week_id=week_id,
            artifacts=result["artifacts"],
            folder_url=result.get("drive_folder_url"),
        )
    except Exception as e:  # noqa: BLE001
        log.exception("Email send failed")
        email_err = str(e)

    return {
        "drafts_count": result["drafts_count"],
        "artifacts": result["artifacts"],
        "drive_folder_url": result.get("drive_folder_url"),
        "email_message_id": email_id,
        "email_error": email_err,
    }


def render_approved(job_id: int) -> dict:
    """Render slides/video/PDF for an approved job and upload to Drive."""
    with db.conn() as c:
        row = c.execute(
            "SELECT week_id, channel, result_json FROM jobs WHERE id=?", (job_id,)
        ).fetchone()
    if not row:
        raise ValueError(f"job {job_id} not found")

    result = json.loads(row["result_json"] or "{}")
    channel = row["channel"]
    week_id = row["week_id"]
    artifacts = result.get("artifacts") or []

    for artifact in artifacts:
        if not artifact.get("needs_render"):
            continue
        slug = artifact.get("slug") or "untitled"
        slides = artifact.get("slides_data") or []
        drive_folder_id = artifact.get("drive_folder_id")
        post_dir = BASE_DIR / (artifact.get("local_folder") or "")
        image_paths: list = []
        errors = artifact.get("errors") or {}

        if slides:
            try:
                aspect = CHANNEL_SIZE.get(channel, "4:5")
                images_dir = post_dir / "images"
                image_paths = render_carousel(slides, images_dir, aspect=aspect, cover_seed=slug)
                log.info("rendered %d images for %s", len(image_paths), slug)
                if drive_folder_id and channel != "linkedin":
                    for p in image_paths:
                        try:
                            up = upload_file(p, drive_folder_id, mimetype="image/png")
                            artifact["image_urls"].append(up.get("file_url") or "")
                        except Exception as e:  # noqa: BLE001
                            errors[f"upload_{p.name}"] = str(e)
                artifact["image_count"] = len(image_paths)
            except Exception as e:  # noqa: BLE001
                log.exception("carousel render failed for %s", slug)
                errors["render"] = str(e)

        if channel == "tiktok" and image_paths:
            try:
                video_path = post_dir / "carousel.mp4"
                build_slideshow_mp4(image_paths, video_path, duration_secs=5)
                if drive_folder_id:
                    up = upload_file(video_path, drive_folder_id, mimetype="video/mp4")
                    artifact["video_file_url"] = up.get("file_url")
            except Exception as e:  # noqa: BLE001
                log.exception("video render failed for %s", slug)
                errors["video"] = str(e)

        if channel == "linkedin" and image_paths:
            try:
                pdf_path = post_dir / "carousel.pdf"
                build_carousel_pdf(image_paths, pdf_path)
                if drive_folder_id:
                    up = upload_file(pdf_path, drive_folder_id, mimetype="application/pdf")
                    artifact["pdf_file_url"] = up.get("file_url")
            except Exception as e:  # noqa: BLE001
                log.exception("pdf render failed for %s", slug)
                errors["pdf"] = str(e)

        artifact["needs_render"] = False
        artifact["errors"] = errors

    result["artifacts"] = artifacts
    result["rendered"] = True
    db.mark_job(job_id, "rendered", result)
    log.info("Render complete for job %d (%s)", job_id, channel)
    return result


def run_forever() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    db.init_db()
    log.info("create_worker started, polling every %ss", POLL_INTERVAL_SECS)
    while True:
        job = db.next_queued_job()
        if not job:
            time.sleep(POLL_INTERVAL_SECS)
            continue
        db.mark_job(job["id"], "running")
        try:
            result = handle(job)
            db.mark_job(job["id"], "done", result)
        except Exception as e:  # noqa: BLE001
            log.exception("Job %s failed", job["id"])
            db.mark_job(job["id"], "failed", {"error": str(e)})


if __name__ == "__main__":
    run_forever()
