"""
5-Day AI Challenge Email Sequence

Reads subscribers from Airtable (source: "ai-challenge"), tracks which day
each subscriber is on via a local JSON file, and sends the appropriate day's
email via Gmail API.

Run daily (cron or manual):
    python challenge_emails.py

Only sends to subscribers who haven't yet received that day's email.
"""

import os
import json
import base64
from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import requests

from gmail_auth import get_gmail_service
from config import ALICE_EMAIL, WEBSITE_URL

# ── Airtable Config (fill in your actual values) ──
AIRTABLE_BASE_ID = os.environ.get("AIRTABLE_BASE_ID", "YOUR_BASE_ID")
AIRTABLE_TABLE_NAME = os.environ.get("AIRTABLE_TABLE_NAME", "Leads")
AIRTABLE_API_KEY = os.environ.get("AIRTABLE_API_KEY", "YOUR_AIRTABLE_API_KEY")

# ── Paths ──
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHALLENGE_DATA_DIR = os.path.join(BASE_DIR, "challenge_data")
SUBSCRIBERS_FILE = os.path.join(CHALLENGE_DATA_DIR, "subscribers.json")

# ── Brand Constants ──
BURGUNDY = "#7D2240"
EGGSHELL = "#F7F3EE"
GOLD = "#C9A847"
GOLD_DK = "#B8952E"
CHARCOAL = "#1C1C1C"
MUTED = "#6B6560"
BOOKING_URL = "https://calendly.com/abazdikian/diagnostic"


# ═══════════════════════════════════════════════════════════════════
# EMAIL TEMPLATES
# ═══════════════════════════════════════════════════════════════════

def _email_wrapper(day_number, day_title, body_html, is_final=False):
    """Wrap day content in the branded email shell."""
    cta_section = ""
    if is_final:
        cta_section = f"""
        <tr><td style="padding:28px 32px;background:{BURGUNDY};border-radius:12px;text-align:center;">
          <p style="font-family:Georgia,'Playfair Display',serif;font-size:20px;font-weight:700;color:{EGGSHELL};margin:0 0 8px;line-height:1.3;">You just completed 5 AI tasks in 5 days.</p>
          <p style="font-size:14px;color:rgba(247,243,238,0.75);margin:0 0 20px;line-height:1.6;">Want to go deeper? Let's talk about what AI can do for your specific business.</p>
          <a href="{BOOKING_URL}" style="display:inline-block;background:{GOLD};color:{CHARCOAL};font-family:Arial,'Inter',sans-serif;font-size:14px;font-weight:700;text-decoration:none;padding:14px 32px;border-radius:100px;">Book a Free Diagnostic Call &rarr;</a>
        </td></tr>
        <tr><td style="height:24px;"></td></tr>
        """
    else:
        cta_section = f"""
        <tr><td style="padding:24px 28px;background:rgba(125,34,64,0.04);border-radius:12px;border-left:3px solid {GOLD};text-align:center;">
          <p style="font-family:Georgia,'Playfair Display',serif;font-size:16px;font-weight:700;color:{CHARCOAL};margin:0 0 6px;">How did it go?</p>
          <p style="font-size:14px;color:{MUTED};margin:0;">Just hit reply and tell me. I read every one.</p>
        </td></tr>
        <tr><td style="height:24px;"></td></tr>
        """

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:{EGGSHELL};font-family:Arial,'Inter',sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:{EGGSHELL};">
    <tr><td align="center" style="padding:32px 16px;">
      <table width="100%" cellpadding="0" cellspacing="0" style="max-width:580px;">

        <!-- Header -->
        <tr><td style="text-align:center;padding:0 0 28px;">
          <p style="font-family:Georgia,'Playfair Display',serif;font-size:22px;font-weight:700;color:{BURGUNDY};margin:0 0 2px;">AB</p>
          <p style="font-size:11px;color:{MUTED};letter-spacing:0.12em;text-transform:uppercase;margin:0;">5-Day AI Challenge</p>
        </td></tr>

        <!-- Divider -->
        <tr><td style="padding:0 0 28px;"><div style="height:2px;background:linear-gradient(90deg,{BURGUNDY},{GOLD});border-radius:2px;"></div></td></tr>

        <!-- Day Badge -->
        <tr><td style="text-align:center;padding:0 0 24px;">
          <div style="display:inline-block;width:56px;height:56px;line-height:56px;border-radius:50%;background:{GOLD};color:{CHARCOAL};font-family:Georgia,'Playfair Display',serif;font-size:24px;font-weight:700;text-align:center;">
            {day_number}
          </div>
        </td></tr>

        <!-- Title -->
        <tr><td style="text-align:center;padding:0 0 8px;">
          <h1 style="font-family:Georgia,'Playfair Display',serif;font-size:26px;font-weight:700;color:{CHARCOAL};margin:0;line-height:1.25;">Day {day_number}: {day_title}</h1>
        </td></tr>

        <!-- Body -->
        <tr><td style="padding:24px 0;">
          {body_html}
        </td></tr>

        <!-- CTA -->
        {cta_section}

        <!-- Footer -->
        <tr><td style="text-align:center;padding:20px 0 0;border-top:1px solid rgba(28,28,28,0.09);">
          <p style="font-size:12px;color:{MUTED};margin:0 0 4px;">Alice Bazdikian &middot; AI Strategist</p>
          <p style="font-size:11px;color:#b0a8a0;margin:0;"><a href="{WEBSITE_URL}" style="color:{BURGUNDY};text-decoration:none;">{WEBSITE_URL}</a></p>
        </td></tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""


def _step_block(steps):
    """Render a numbered step list."""
    html = ""
    for i, step in enumerate(steps, 1):
        html += f"""
        <tr><td style="padding:8px 0;">
          <table cellpadding="0" cellspacing="0"><tr>
            <td style="vertical-align:top;padding-right:12px;">
              <div style="display:inline-block;width:28px;height:28px;line-height:28px;border-radius:50%;background:{BURGUNDY};color:{EGGSHELL};font-size:13px;font-weight:700;text-align:center;">{i}</div>
            </td>
            <td style="font-size:15px;color:{CHARCOAL};line-height:1.6;">{step}</td>
          </tr></table>
        </td></tr>"""
    return f'<table width="100%" cellpadding="0" cellspacing="0">{html}</table>'


def _prompt_block(prompt_text):
    """Render a copy-paste prompt example."""
    return f"""
    <table width="100%" cellpadding="0" cellspacing="0" style="margin:16px 0;">
      <tr><td style="padding:18px 20px;background:#FFFFFF;border:1px solid rgba(28,28,28,0.09);border-left:3px solid {GOLD};border-radius:0 10px 10px 0;">
        <p style="font-size:10px;font-weight:700;color:{GOLD};letter-spacing:0.1em;text-transform:uppercase;margin:0 0 8px;">Copy &amp; paste this prompt</p>
        <p style="font-size:14px;color:{CHARCOAL};line-height:1.65;margin:0;font-family:'Courier New',monospace;">{prompt_text}</p>
      </td></tr>
    </table>"""


# ── Day 1 ──
DAY_1_BODY = (
    f'<p style="font-size:15px;color:{CHARCOAL};line-height:1.7;margin:0 0 20px;">Welcome to the challenge! Today is about taking the first step. No prep needed. Just open Claude and have a real conversation about your business.</p>'
    + _step_block([
        'Go to <a href="https://claude.ai" style="color:{};font-weight:600;text-decoration:none;">claude.ai</a> and create a free account (if you haven\'t already).'.format(BURGUNDY),
        "Think of one real question you have about your business right now.",
        "Type it into Claude exactly as you'd ask a colleague.",
        "Read the response. Then ask a follow-up question to go deeper.",
    ])
    + _prompt_block(
        "I run a [type of business] with [X] employees. "
        "My biggest challenge right now is [describe challenge]. "
        "What are 3 practical things I could do this week to address it?"
    )
)

# ── Day 2 ──
DAY_2_BODY = (
    f'<p style="font-size:15px;color:{CHARCOAL};line-height:1.7;margin:0 0 20px;">Yesterday you had your first conversation. Today, let\'s make Claude do something useful: draft a client email you\'d actually send.</p>'
    + _step_block([
        "Pick a client email you need to write (follow-up, proposal, check-in, etc.).",
        "Give Claude the context: who the client is, what you need to say, and the tone you want.",
        "Review the draft. Edit anything that doesn't sound like you.",
        "Send it. (Yes, actually send it.)",
    ])
    + _prompt_block(
        "I need to write a [type of email] to [client name/description]. "
        "Context: [brief background]. "
        "Tone: [professional/friendly/direct]. "
        "Key points to include: [list 2-3 points]. "
        "Keep it under 150 words."
    )
)

# ── Day 3 ──
DAY_3_BODY = (
    f'<p style="font-size:15px;color:{CHARCOAL};line-height:1.7;margin:0 0 20px;">You\'ve seen Claude write one email. Now let\'s build something you\'ll use over and over: a reusable template for something you write repeatedly.</p>'
    + _step_block([
        "Pick something you write at least once a week (proposals, follow-ups, onboarding emails, SOPs).",
        "Give Claude an example of one you've written before (paste it in).",
        "Ask it to create a template with fill-in-the-blank sections.",
        "Save the template somewhere you'll actually use it.",
    ])
    + _prompt_block(
        "Here's an example of a [type of document] I've written before: "
        "[paste your example]. "
        "Create a reusable template based on this with [brackets] for the parts that change each time. "
        "Keep my voice and style. Add any sections I might be missing."
    )
)

# ── Day 4 ──
DAY_4_BODY = (
    f'<p style="font-size:15px;color:{CHARCOAL};line-height:1.7;margin:0 0 20px;">Today gets strategic. You\'re going to use Claude as a business analyst to look at your competition with fresh eyes.</p>'
    + _step_block([
        "Pick a competitor whose website you know well.",
        "Copy the text from their homepage (or paste the URL if using Claude Pro).",
        "Ask Claude to analyze it against your positioning.",
        "Pick one insight to act on this week.",
    ])
    + _prompt_block(
        "Here's the homepage copy from my competitor [name]: [paste text]. "
        "My business is [describe your business and what makes you different]. "
        "Tell me: 3 things they do better than me on their website, "
        "3 opportunities where I could differentiate, "
        "and 1 specific change I should make to my own messaging this week."
    )
)

# ── Day 5 ──
DAY_5_BODY = (
    f'<p style="font-size:15px;color:{CHARCOAL};line-height:1.7;margin:0 0 20px;">Final day. This is where it clicks. You\'re going to take your most tedious recurring task and create a simple AI workflow for it.</p>'
    + _step_block([
        "List your top 3 most repetitive weekly tasks (invoicing, social posts, report summaries, etc.).",
        "Pick the one that's most annoying and describe it step-by-step to Claude.",
        "Ask Claude to create a workflow: what you do, what Claude handles, and the exact prompts to use each time.",
        "Run through the workflow once right now to test it.",
    ])
    + _prompt_block(
        "Every week I have to [describe the task in detail]. "
        "It usually takes me [time] and involves [steps]. "
        "Create a simple workflow where I do the minimum and Claude handles the rest. "
        "Include the exact prompts I should use each time, "
        "and tell me what info I need to gather before starting."
    )
)


CHALLENGE_EMAILS = {
    1: {
        "subject": "Day 1: Your First AI Conversation",
        "html": _email_wrapper(1, "Your First AI Conversation", DAY_1_BODY),
    },
    2: {
        "subject": "Day 2: Draft a Client Email",
        "html": _email_wrapper(2, "Draft a Client Email", DAY_2_BODY),
    },
    3: {
        "subject": "Day 3: Build a Template",
        "html": _email_wrapper(3, "Build a Template", DAY_3_BODY),
    },
    4: {
        "subject": "Day 4: Analyze Your Competitor",
        "html": _email_wrapper(4, "Analyze Your Competitor", DAY_4_BODY),
    },
    5: {
        "subject": "Day 5: Automate One Task",
        "html": _email_wrapper(5, "Automate One Task", DAY_5_BODY, is_final=True),
    },
}


# ═══════════════════════════════════════════════════════════════════
# SUBSCRIBER TRACKING
# ═══════════════════════════════════════════════════════════════════

def load_subscribers():
    """Load subscriber tracking data from local JSON file."""
    if os.path.exists(SUBSCRIBERS_FILE):
        with open(SUBSCRIBERS_FILE, "r") as f:
            return json.load(f)
    return {}


def save_subscribers(data):
    """Save subscriber tracking data to local JSON file."""
    os.makedirs(CHALLENGE_DATA_DIR, exist_ok=True)
    with open(SUBSCRIBERS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def fetch_challenge_subscribers():
    """Fetch subscribers with source 'ai-challenge' from Airtable."""
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json",
    }
    params = {
        "filterByFormula": "{Source}='ai-challenge'",
        "fields[]": ["Email", "Source", "Timestamp"],
    }

    all_records = []
    offset = None

    while True:
        if offset:
            params["offset"] = offset

        resp = requests.get(url, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()

        all_records.extend(data.get("records", []))
        offset = data.get("offset")

        if not offset:
            break

    emails = []
    for record in all_records:
        email = record.get("fields", {}).get("Email", "").strip().lower()
        if email:
            emails.append(email)

    return emails


# ═══════════════════════════════════════════════════════════════════
# EMAIL SENDING
# ═══════════════════════════════════════════════════════════════════

def send_challenge_email(service, to_email, day_number):
    """Send a single challenge email for the given day."""
    email_data = CHALLENGE_EMAILS[day_number]

    msg = MIMEMultipart("alternative")
    msg["to"] = to_email
    msg["from"] = ALICE_EMAIL
    msg["subject"] = email_data["subject"]

    plain = (
        f"Day {day_number} of the 5-Day AI Challenge. "
        f"View this email in HTML for the full experience."
    )
    msg.attach(MIMEText(plain, "plain", "utf-8"))
    msg.attach(MIMEText(email_data["html"], "html", "utf-8"))

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
    sent = service.users().messages().send(
        userId="me", body={"raw": raw}
    ).execute()

    return sent["id"]


# ═══════════════════════════════════════════════════════════════════
# MAIN RUNNER
# ═══════════════════════════════════════════════════════════════════

def run_challenge():
    """
    Main entry point. Fetches subscribers, determines which day each is on,
    sends the next email, and updates tracking.
    """
    now = datetime.now(timezone.utc).isoformat()

    # 1. Fetch current challenge subscribers from Airtable
    print("[Challenge] Fetching subscribers from Airtable...")
    try:
        airtable_emails = fetch_challenge_subscribers()
    except Exception as e:
        print(f"[Challenge] ERROR fetching from Airtable: {e}")
        print("[Challenge] Falling back to existing subscriber list.")
        airtable_emails = []

    # 2. Load local tracking data
    subscribers = load_subscribers()

    # 3. Add any new subscribers
    new_count = 0
    for email in airtable_emails:
        if email not in subscribers:
            subscribers[email] = {
                "current_day": 0,
                "emails_sent": {},
                "enrolled_at": now,
            }
            new_count += 1

    if new_count:
        print(f"[Challenge] {new_count} new subscriber(s) added.")

    # 4. Authenticate Gmail
    print("[Challenge] Authenticating with Gmail...")
    service = get_gmail_service()

    # 5. Send emails
    sent_count = 0
    completed_count = 0

    for email, data in subscribers.items():
        current_day = data["current_day"]
        next_day = current_day + 1

        # Skip if already completed all 5 days
        if next_day > 5:
            completed_count += 1
            continue

        # Skip if already sent today's email
        if str(next_day) in data.get("emails_sent", {}):
            continue

        # Send the next day's email
        try:
            msg_id = send_challenge_email(service, email, next_day)
            data["current_day"] = next_day
            data.setdefault("emails_sent", {})[str(next_day)] = {
                "sent_at": now,
                "message_id": msg_id,
            }
            sent_count += 1
            print(f"  [Day {next_day}] Sent to {email} (msg: {msg_id})")
        except Exception as e:
            print(f"  [ERROR] Failed to send Day {next_day} to {email}: {e}")

    # 6. Save updated tracking
    save_subscribers(subscribers)

    print(f"\n[Challenge] Done. Sent {sent_count} email(s). "
          f"{completed_count} subscriber(s) already completed. "
          f"{len(subscribers)} total subscriber(s) tracked.")


if __name__ == "__main__":
    run_challenge()
