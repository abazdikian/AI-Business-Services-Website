"""
Orchestrator: parse reply → load digest → render graphics → upload → confirm.
"""

import os
import json
import re
import sys
from datetime import datetime

from config import LATEST_DIGEST_FILE, OUTPUT_DIR
from monitor_reply import check_for_reply
from render_graphics import render_post
from upload_drive import upload_post_graphics
from send_email import send_email


def _slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s]+', '-', text)
    return text[:50].rstrip('-')


def _load_digest():
    try:
        with open(LATEST_DIGEST_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"[ERROR] Could not load digest: {e}")
        return []


def generate_graphics(selected_indices=None):
    """Generate graphics for selected items. If no indices, check for reply."""
    if selected_indices is None:
        selected_indices = check_for_reply()
        if not selected_indices:
            print("[Generate] No reply with picks found.")
            return

    items = _load_digest()
    if not items:
        print("[Generate] No digest data found.")
        return

    week_label = f"Week of {datetime.now().strftime('%Y-%m-%d')}"
    week_dir = os.path.join(OUTPUT_DIR, week_label.replace(" ", "-").lower())
    os.makedirs(week_dir, exist_ok=True)

    generated = []
    drive_links = []

    for idx in selected_indices:
        if idx < 0 or idx >= len(items):
            print(f"[WARN] Index {idx} out of range, skipping")
            continue

        item = items[idx]
        slug = f"{idx+1}-{_slugify(item.get('headline', 'post'))}"
        post_dir = os.path.join(week_dir, slug)

        print(f"\n--- Rendering: {item.get('headline', '')} ---")

        try:
            result = render_post(item, post_dir)
            generated.append({
                "index": idx + 1,
                "headline": item.get("headline", ""),
                "png": result["png"],
                "pdf": result["pdf"],
            })

            drive_url = upload_post_graphics(post_dir, slug, week_label)
            if drive_url:
                drive_links.append({"headline": item.get("headline", ""), "url": drive_url})

        except Exception as e:
            print(f"[ERROR] Failed: {e}")
            continue

    if generated:
        _send_confirmation(generated, drive_links)

    print(f"\n{'='*60}")
    print(f"DONE — {len(generated)} posts rendered")
    print(f"{'='*60}")


def _send_confirmation(generated, drive_links):
    """Send confirmation email with list of generated graphics."""
    items_html = ""
    for g in generated:
        drive_link = ""
        for dl in drive_links:
            if dl["headline"] == g["headline"]:
                drive_link = f' · <a href="{dl["url"]}" style="color:#C9A847;">View in Drive</a>'
                break
        items_html += (
            f'<tr><td style="padding:8px 0;border-bottom:1px solid rgba(28,28,28,0.06);">'
            f'<span style="font-weight:600;color:#1C1C1C;">{g["index"]}. {g["headline"]}</span>'
            f'<span style="font-size:12px;color:#6B6560;"> — PNG{"+ PDF" if g["pdf"] else ""}{drive_link}</span>'
            f'</td></tr>'
        )

    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#F7F3EE;font-family:Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#F7F3EE;">
<tr><td align="center" style="padding:32px 16px;">
<table width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;">
<tr><td style="text-align:center;padding:0 0 24px;">
<p style="font-family:Georgia,serif;font-size:22px;font-weight:700;color:#7D2240;margin:0 0 4px;">AB</p>
<h1 style="font-family:Georgia,serif;font-size:24px;font-weight:700;color:#1C1C1C;margin:0;">Your graphics are ready</h1>
<p style="font-size:13px;color:#6B6560;margin:4px 0 0;">{len(generated)} posts · {datetime.now().strftime('%B %d, %Y')}</p>
</td></tr>
<tr><td><div style="height:2px;background:linear-gradient(90deg,#7D2240,#C9A847);border-radius:2px;margin-bottom:20px;"></div></td></tr>
<tr><td><table width="100%" cellpadding="0" cellspacing="0">{items_html}</table></td></tr>
<tr><td style="text-align:center;padding:24px 0 0;">
<p style="font-size:13px;color:#6B6560;">Graphics saved locally and uploaded to Google Drive.</p>
</td></tr></table></td></tr></table></body></html>"""

    try:
        send_email(f"Your graphics are ready — {len(generated)} posts", html)
    except Exception as e:
        print(f"[WARN] Confirmation email failed: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Manual mode: python3 generate_from_reply.py 1 3 5 7
        indices = [int(n) - 1 for n in sys.argv[1:]]
        generate_graphics(indices)
    else:
        # Auto mode: check for reply
        generate_graphics()
