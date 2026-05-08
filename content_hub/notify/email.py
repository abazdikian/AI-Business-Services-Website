"""Send an approval email for a finished drafts batch.

Accepts a list of `artifacts` from the worker. Two shapes:
  kind=draft   → LI/TT/IG: one Alice-voice post per file
  kind=video   → YouTube:  per-video folder (transcript + description + deck)
"""

import base64
import html
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from ..config import ALICE_EMAIL
from .google import gmail_service

log = logging.getLogger(__name__)
PREVIEW_CHARS = 260


# ---------------------------------------------------------------
# Text / HTML helpers
# ---------------------------------------------------------------

def _btn(href: str, label: str) -> str:
    return (
        f'<a href="{html.escape(href)}" '
        f'style="display:inline-block;background:#7A1F2B;color:white;'
        f'padding:7px 14px;border-radius:6px;text-decoration:none;'
        f'font-weight:600;font-size:12.5px;margin-right:8px;">{label}</a>'
    )


def _link(href: str, label: str) -> str:
    return (
        f'<a href="{html.escape(href)}" '
        f'style="color:#7A1F2B;text-decoration:none;border-bottom:1px solid #C9A24B;'
        f'font-size:12.5px;margin-right:14px;">{label}</a>'
    )


def _post_card(a: dict) -> str:
    hook = html.escape(a.get("title") or "Untitled")
    slides = a.get("slides_count", 0)
    images = a.get("image_count", 0)
    preview = html.escape(a.get("caption_preview") or "").replace("\n", "<br>")
    meta_bits = []
    if a.get("creator"):
        meta_bits.append(f"Inspired by @{html.escape(a['creator'])}")
    meta_bits.append(f"{slides}-slide carousel")
    if images:
        meta_bits.append(f"{images} PNG{'s' if images != 1 else ''} rendered")
    if a.get("source_url"):
        meta_bits.append(f'<a href="{html.escape(a["source_url"])}">source</a>')
    meta = " · ".join(meta_bits)

    links = []
    if a.get("drive_folder_url"):
        links.append(_btn(a["drive_folder_url"], "Open folder →"))

    errors = a.get("errors") or {}
    err_html = ""
    if errors:
        items = "".join(f"<li>{html.escape(k)}: {html.escape(v)}</li>"
                        for k, v in errors.items())
        err_html = (
            f'<ul style="color:#8A2020;font-size:12.5px;margin:10px 0 0;'
            f'padding-left:18px;">{items}</ul>'
        )

    return f"""
    <section style="margin:0 0 28px;padding:22px 26px;background:white;
                    border:1px solid #E7DED2;border-radius:12px;">
      <div style="color:#7A1F2B;font-family:Georgia,serif;font-size:18px;
                  margin-bottom:4px;">{hook}</div>
      <div style="color:#7A6E63;font-size:12.5px;margin-bottom:12px;">{meta}</div>
      <div>{''.join(links)}</div>
      {err_html}
    </section>"""


def _video_card(a: dict) -> str:
    title = html.escape(a.get("title") or "Untitled video")
    creator = html.escape(a.get("creator") or "")
    sections = a.get("section_count", 0)
    errors = a.get("errors") or {}

    links = []
    if a.get("slides_url"):
        links.append(_btn(a["slides_url"], "Open talking deck →"))
    if a.get("drive_folder_url"):
        links.append(_btn(a["drive_folder_url"], "Open folder →"))

    err_html = ""
    if errors:
        items = "".join(f"<li>{html.escape(k)}: {html.escape(v)}</li>"
                        for k, v in errors.items())
        err_html = (
            f'<ul style="color:#8A2020;font-size:12.5px;margin:10px 0 0;'
            f'padding-left:18px;">{items}</ul>'
        )

    return f"""
    <section style="margin:0 0 28px;padding:22px 26px;background:white;
                    border:1px solid #E7DED2;border-radius:12px;">
      <div style="color:#7A1F2B;font-family:Georgia,serif;font-size:18px;
                  margin-bottom:4px;">{title}</div>
      <div style="color:#7A6E63;font-size:12.5px;margin-bottom:14px;">
        @{creator} · {sections} sections
      </div>
      <div>{''.join(links)}</div>
      {err_html}
    </section>"""


def _html_body(channel: str, week_id: str, artifacts: list[dict],
               folder_url: str | None) -> str:
    cards = []
    for a in artifacts:
        if a.get("kind") == "video":
            cards.append(_video_card(a))
        else:
            cards.append(_post_card(a))

    drive_block = (
        f'<p style="margin:0 0 22px;">{_btn(folder_url, "Open channel folder →")}</p>'
        if folder_url else ""
    )

    return f"""
    <html><body style="margin:0;background:#F7F3EE;padding:32px 0;
                        font-family:-apple-system,Helvetica,Arial,sans-serif;">
      <div style="max-width:680px;margin:0 auto;padding:0 20px;">
        <h1 style="color:#7A1F2B;font-family:Georgia,serif;font-size:26px;
                   margin:0 0 4px;">Content Hub — {html.escape(channel).capitalize()}</h1>
        <p style="color:#7A6E63;font-size:13.5px;margin:0 0 20px;">
          Week {html.escape(week_id)} · {len(artifacts)} item{'s' if len(artifacts)!=1 else ''} ready for review
        </p>
        {drive_block}
        {''.join(cards)}
        <p style="color:#7A6E63;font-size:12px;margin-top:28px;">
          Generated locally by Content Hub · reply to flag anything off-voice.
        </p>
      </div>
    </body></html>
    """


def _plain_body(channel: str, week_id: str, artifacts: list[dict],
                folder_url: str | None) -> str:
    out = [f"Content Hub — {channel} — week {week_id}", "=" * 48, ""]
    if folder_url:
        out.append(f"Folder: {folder_url}")
        out.append("")
    for a in artifacts:
        if a.get("kind") == "video":
            out.append(f"• VIDEO: {a.get('title')}")
            if a.get("slides_url"):
                out.append(f"    deck:        {a['slides_url']}")
            if a.get("errors"):
                for k, v in a["errors"].items():
                    out.append(f"    ! {k}: {v}")
        else:
            imgs = a.get("image_count", 0)
            out.append(
                f"• POST: {a.get('title')}  ({a.get('slides_count', 0)}-slide carousel, {imgs} PNGs)"
            )
            if a.get("drive_folder_url"):
                out.append(f"    folder: {a['drive_folder_url']}")
            if a.get("errors"):
                for k, v in a["errors"].items():
                    out.append(f"    ! {k}: {v}")
        out.append("")
    return "\n".join(out)


# ---------------------------------------------------------------
# public
# ---------------------------------------------------------------

def send_drafts_email(*, channel: str, week_id: str, artifacts: list[dict],
                      folder_url: str | None) -> str:
    svc = gmail_service()
    item_count = len(artifacts)

    if channel == "youtube":
        subject = (
            f"Content Hub — YouTube · {item_count} video"
            f"{'s' if item_count != 1 else ''} with decks ({week_id})"
        )
    else:
        subject = (
            f"Content Hub — {channel.capitalize()} · {item_count} draft"
            f"{'s' if item_count != 1 else ''} ready ({week_id})"
        )

    msg = MIMEMultipart("alternative")
    msg["to"] = ALICE_EMAIL
    msg["from"] = ALICE_EMAIL
    msg["subject"] = subject

    msg.attach(MIMEText(_plain_body(channel, week_id, artifacts, folder_url),
                        "plain", "utf-8"))
    msg.attach(MIMEText(_html_body(channel, week_id, artifacts, folder_url),
                        "html", "utf-8"))

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
    sent = svc.users().messages().send(userId="me", body={"raw": raw}).execute()
    log.info("Email sent id=%s", sent["id"])
    return sent["id"]
