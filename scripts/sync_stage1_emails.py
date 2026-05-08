#!/usr/bin/env python3
"""Build Stage 1 nurture sequence in Buttondown.

Reads email copy from this file (with em-dash sweep + 2b softening + 2c cut
+ Email 1 link-only swap + 6pm->7pm time corrections all already applied),
creates 6 email drafts via API, then wires them into a single inactive
automation that triggers on `lead-magnet-3-workflows` tag and stops on
`webinar-2026-06-03` tag.

Idempotent-ish: if any email subject already exists, we skip its creation
and reuse the existing email.
"""
import os
import sys
import json
import urllib.request
import urllib.error

API = "https://api.buttondown.email/v1"
KEY = os.environ["BUTTONDOWN_API_KEY"]

TRIGGER_TAG_ID = "sub_tag_385drckksg9d4tk1kseyhrt6ev"  # lead-magnet-3-workflows
STOP_TAG_ID    = "sub_tag_27dw7va8918rkv8acmb3qtmacj"  # webinar-2026-06-03

# Buttondown template syntax for first name with fallback.
NAME = "{{ subscriber.metadata.first_name | default('there') }}"

EMAILS = [
    # -- EMAIL 1, day 0 --
    {
        "subject": "Your kit is here (and one workflow you should run today)",
        "body": f"""Hey {NAME},

Your 3-Workflow Starter Kit is here:
https://www.smallbusinessaicoach.com/assets/lead-magnets/3-workflows-starter-kit.pdf

Bookmark it. You'll come back to it.

Here's how I'd actually use it:

Don't read all 14 pages tonight. Pick the workflow that matches your loudest current pain (most owners pick #1, Inbox Triage). Set aside 20 minutes tomorrow morning. Copy the prompt. Run it on 8 real emails. Time how long the whole thing takes.

If it works, you'll have your first hour back by lunch.

One more thing: there's a surprise bonus workflow on page 11. It's the one that answers the loudest small-business pain on Reddit right now. Open the PDF, it's the one nobody else is teaching.

Tomorrow I'll send you the part that DIDN'T make it into the kit (a small mistake most owners make running Workflow #1). That's the email you'll want to read.

Talk soon,
Alice

P.S. The free live workshop on June 3 is the natural next step after the kit. I run the audit on a real attendee's business and build all 3 workflows in front of you. 50 seats only, no public replay. https://www.smallbusinessaicoach.com/webinar
""",
        "delay_days": 0,
    },
    # -- EMAIL 2, day 2 --
    {
        "subject": "The mistake almost everyone makes with Workflow #1",
        "body": f"""Hey {NAME},

Quick story.

I have a client (an accountant, 6-person firm) who downloaded a guide like this kit a few months ago. She set up Workflow #1 (Inbox Triage), loved it, and within a week was auto-sending Claude's draft replies straight from her inbox.

Two weeks later, a long-time client received a polite, perfectly-worded reply that was almost the right answer. Almost. The numbers were right but the tone was 5% too formal for the relationship. The client noticed. She apologized. It was awkward.

She still uses Workflow #1. She just adds 5 seconds.

Here's the rule: AI is good at 80% of replies. The last 20% is you reading the relationship. Read every draft before you send. Five seconds per email beats five minutes of typing it from scratch, AND it beats one awkward "almost right" reply that costs you a $30k retainer.

If you've already set up Workflow #1, you're ahead of most people who downloaded the kit. If you haven't yet, today's a good day. Page 3 of the PDF.

Tomorrow I'll send you the workflow most owners ignore (it's also the one that makes the other three 3x better).

Alice

P.S. If you want me to walk through these workflows live on YOUR business, the free workshop is June 3 at 7pm ET. https://www.smallbusinessaicoach.com/webinar
""",
        "delay_days": 2,
    },
    # -- EMAIL 3, day 5 --
    {
        "subject": "Why 9 out of 10 AI implementations stall at the same place",
        "body": f"""Hey {NAME},

Most small business owners I talk to have a similar AI story.

Week 1: They try ChatGPT or Claude. It's magic. They tell their team about it.
Week 2: They use it for one or two things. Email drafts, mostly.
Week 3: They start re-pasting the same context into every conversation. "I run a 4-person dental practice. Our brand voice is warm and direct. Our patients are mostly..."
Week 4: They stop using it. Not because it didn't work. Because re-pasting context every time felt like the work the AI was supposed to remove.

This is where 9 out of 10 small biz AI implementations stall. Not at "AI is too complex." At "I'm tired of re-explaining my business every time."

Workflow #2 (the SOP-to-AI-Trainer, page 5 of the kit) is the fix. You upload your existing SOP, brand voice, pricing, FAQ docs into a Claude Project once. From then on, every conversation in that project pulls your business context automatically. No more re-pasting.

This is also the move that makes Workflows #1, #3, and #4 work properly. Once Claude knows your business, the inbox triage replies sound like YOU. The marketing loop generates content in YOUR voice. The invoice extraction knows your suppliers and your accounting setup.

If you only build ONE of the four workflows in the kit this week, build #2.

The reason this matters for the workshop: on June 3 we set up Workflow #2 LIVE on a real attendee's business. You watch it happen, then you do the same thing on yours that night. By June 4, your AI knows your business. That's the unlock.

50 seats only. No public replay. https://www.smallbusinessaicoach.com/webinar

Alice
""",
        "delay_days": 5,
    },
    # -- EMAIL 4, day 8 --
    {
        "subject": "What 12 hours back actually feels like",
        "body": f"""Hey {NAME},

I'm going to do something unusual: I'm going to tell you what NOT having these workflows feels like, then what HAVING them feels like. Both are real.

Without:
You wake up Sunday with a knot in your stomach because you know there are 47 emails you haven't replied to, two follow-ups you forgot, a newsletter you meant to write, and an invoice you can't find. You spend the morning catching up on Sunday what you should've handled on Tuesday. Monday starts already behind. Repeat weekly.

With:
You sit down Monday morning. Your inbox is triaged before your coffee is poured (Workflow #1). Your follow-ups are tracked in a doc Claude maintains (a small extension of Workflow #2). The newsletter you said you'd write is already drafted, in your voice, waiting for a 5-minute edit (Workflow #3). The supplier invoices that came in over the weekend are already in your accounting software (Workflow #4). You start your week creating, not catching up.

The math from one Accelerator client (a 4-person consultancy) over her first 30 days:
  - 5 hrs/week back from inbox triage
  - 3 hrs/week back from the project setup
  - 4 hrs/week back from the weekly marketing loop
  - 2 hrs/week back from the invoice workflow
Total: about 14 hrs/week. Almost two full work-days.

She put those 14 hours into one new client every week. Math: about $8k/mo more revenue, no extra hires.

You don't have to take my word for it. Run Workflow #1 today. See if it gets you 5 hours back this week. That's the test.

If you want me to walk you through Implement + Run live on YOUR business, the free workshop on June 3 is where I do that.

Alice

P.S. The workshop also includes one bonus I don't put on the public page: a private prompt vault (40+ prompts I personally use). Live attendees only. https://www.smallbusinessaicoach.com/webinar
""",
        "delay_days": 8,
    },
    # -- EMAIL 5, day 11 --
    {
        "subject": "What we're going to do live on June 3",
        "body": f"""Hey {NAME},

We're 9 days out from the live workshop. Here's exactly what's going to happen:

7:00 - I open with the lie you've been told about AI. (It's not "use ChatGPT more.")

7:05 - We do the A.I.R. Audit live on one volunteer's business. Anyone who RSVPs can volunteer. I pick one. Doesn't matter what kind of business.

7:25 - I build 3 workflows on that business in front of you. Same workflows from your kit, but actually wired into someone's real ops, in real time. You're following along on yours.

7:45 - I show you exactly how to run this for the next 30 days. The Accelerator gets a 5-minute mention here. If you're not interested, just close the tab.

7:55 - Live Q&A. I stay until the last hand drops.

The question I want you to bring: "If AI gave me back 5 hours next Tuesday, what would I actually use them for?" Most owners can't answer this. The ones who can are the ones who win with AI.

50 live seats. Last time I checked, about a quarter were gone. I'd grab yours this week. https://www.smallbusinessaicoach.com/webinar

Alice

P.S. One thing I forgot to mention: I email a personal 30-day roadmap to every live attendee within 24 hours of the workshop. Built around your business, not generic. Not on the page, but it's part of the deal.
""",
        "delay_days": 11,
    },
    # -- EMAIL 6, day 13 --
    {
        "subject": "Tomorrow is the last day to RSVP for the workshop",
        "body": f"""Hey {NAME},

Quick note: RSVP for the June 3 workshop closes tomorrow at 11:59pm ET, or when 50 seats fill. Whichever comes first.

If you've been on the fence, here's the honest test:

Open your kit PDF. Did you actually run Workflow #1 yet? If yes, you're already getting value from the work alone. The workshop is the next step (live build, not a video).

If no, why not? It's usually one of:
  - "I'll get to it later" (you won't)
  - "I want someone to walk me through it" (that's the workshop)
  - "I'm not sure it'll work for MY business" (the workshop is built around one volunteer's business, live, so you see exactly how it adapts)

Whichever bucket you're in, the workshop is the unblock. Free. 60 minutes. Wed June 3 at 7pm ET. Live on Zoom. Capped at 50.

Save your seat: https://www.smallbusinessaicoach.com/webinar

After tomorrow, I close the door. The replay only goes to live attendees. There's no "I'll catch the replay" path.

Alice
""",
        "delay_days": 13,
    },
]


def api(method, path, data=None):
    url = API + path
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(
        url, data=body, method=method,
        headers={
            "Authorization": f"Token {KEY}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read() or b"null")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"null")


def find_email_by_subject(subject):
    """Search existing emails by subject so we don't duplicate on re-runs."""
    code, data = api("GET", f"/emails?limit=100")
    if code != 200:
        return None
    for e in data.get("results", []):
        if e.get("subject") == subject:
            return e["id"]
    return None


# 1. Create or reuse 6 emails
print("=== creating emails ===")
email_ids = []
for i, e in enumerate(EMAILS, 1):
    existing = find_email_by_subject(e["subject"])
    if existing:
        print(f"  [{i}] reused: {existing}  {e['subject']}")
        email_ids.append(existing)
        continue
    code, data = api("POST", "/emails", {
        "subject": e["subject"],
        "body": e["body"],
        "email_type": "public",
        "status": "draft",  # held for automation use, not auto-sent
    })
    if code not in (200, 201):
        print(f"  [{i}] FAILED ({code}): {data}")
        sys.exit(1)
    email_ids.append(data["id"])
    print(f"  [{i}] created: {data['id']}  {e['subject']}")

# 2. Build automation
print("\n=== building automation ===")
actions = [
    {
        "type": "send_email",
        "metadata": {"email_id": eid, "delay_days": e["delay_days"]},
    }
    for eid, e in zip(email_ids, EMAILS)
]

automation_payload = {
    "name": "Stage 1 - 3-Workflow Kit nurture to June 3 webinar",
    "trigger": "subscriber.tags.changed",
    "actions": actions,
    # Filter: only fire when the trigger tag is added,
    # AND the subscriber does NOT already have the stop tag.
    "filters": {
        "predicate": "and",
        "filters": [
            {
                "field": "tags",
                "operator": "contains",
                "value": TRIGGER_TAG_ID,
            },
            {
                "field": "tags",
                "operator": "not_contains",
                "value": STOP_TAG_ID,
            },
        ],
        "groups": [],
    },
    # Re-evaluate the filter at each step so subscribers who acquire
    # the stop tag mid-sequence (e.g. RSVP for the webinar between
    # Email 2 and Email 3) are dropped before the next email sends.
    "should_evaluate_filter_after_delay": True,
}

code, data = api("POST", "/automations", automation_payload)
if code not in (200, 201):
    print(f"  FAILED ({code}): {json.dumps(data, indent=2)}")
    sys.exit(1)

print(f"  created: {data['id']}")
print(f"  status:  {data.get('status')}")
print(f"  filter eval after delay: {data.get('should_evaluate_filter_after_delay')}")
print(f"  action count: {len(data.get('actions', []))}")
print(f"\nAll done. Open Buttondown UI to preview emails before enabling.")
