"""
Weekly Instagram Scout — scrapes top posts from monitored accounts,
filters for relevance, and drafts content suggestions.

Usage: python scout_instagram.py
"""

import os
import sys
import json
import time
import requests
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
from config import ALICE_EMAIL

APIFY_TOKEN = os.environ.get("APIFY_API_TOKEN", "")
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# ── Accounts to monitor ──
ACCOUNTS = {
    "AI Automation": [
        "nick_saraev",
        "sabrina_ramonov",
        "chase.h.ai",
        "nateherkai",
        "nicholas.puru",
    ],
    "AI Tools & Tutorials": [
        "nathanhodgson.ai",
        "zeeeljain",
        "adamstewartmarketing",
        "digitalsamaritan",
        "wright_mode",
    ],
    "Vibe Coding": [
        "realrileybrown",
        "khris.sheer",
        "byjackprice",
    ],
}

POSTS_PER_ACCOUNT = 3
MIN_LIKES = 50  # minimum engagement threshold


def scrape_account(username):
    """Scrape latest posts from an Instagram account via Apify."""
    if not APIFY_TOKEN:
        print(f"  [SKIP] No APIFY_API_TOKEN set")
        return []

    url = "https://api.apify.com/v2/acts/apify~instagram-scraper/runs"
    headers = {
        "Authorization": f"Bearer {APIFY_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "directUrls": [f"https://www.instagram.com/{username}/"],
        "resultsType": "posts",
        "resultsLimit": POSTS_PER_ACCOUNT,
    }

    # Start the run
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        if r.status_code != 201:
            print(f"  [ERR] @{username}: {r.status_code} {r.text[:200]}")
            return []
        run_data = r.json().get("data", {})
        run_id = run_data.get("id")
        dataset_id = run_data.get("defaultDatasetId")
    except Exception as e:
        print(f"  [ERR] @{username}: {e}")
        return []

    # Poll for completion
    for _ in range(30):
        try:
            status_r = requests.get(
                f"https://api.apify.com/v2/actor-runs/{run_id}",
                headers={"Authorization": f"Bearer {APIFY_TOKEN}"},
                timeout=15,
            )
            status = status_r.json().get("data", {}).get("status", "")
            if status == "SUCCEEDED":
                break
            if status in ("FAILED", "ABORTED", "TIMED-OUT"):
                print(f"  [ERR] @{username}: run {status}")
                return []
        except:
            pass
        time.sleep(2)

    # Fetch results
    try:
        items_r = requests.get(
            f"https://api.apify.com/v2/datasets/{dataset_id}/items",
            headers={"Authorization": f"Bearer {APIFY_TOKEN}"},
            timeout=30,
        )
        posts = items_r.json()
    except Exception as e:
        print(f"  [ERR] @{username} fetch: {e}")
        return []

    results = []
    for post in posts:
        likes = post.get("likesCount", 0) or 0
        if likes < MIN_LIKES:
            continue
        results.append({
            "username": post.get("ownerUsername", username),
            "caption": post.get("caption", ""),
            "likes": likes,
            "comments": post.get("commentsCount", 0) or 0,
            "url": post.get("url", ""),
            "type": post.get("type", ""),
            "images": len(post.get("images", [])),
            "timestamp": post.get("timestamp", ""),
        })

    return results


def scrape_all():
    """Scrape all monitored accounts."""
    all_posts = []
    for category, usernames in ACCOUNTS.items():
        print(f"\n── {category} ──")
        for username in usernames:
            print(f"  Scraping @{username}...")
            posts = scrape_account(username)
            for p in posts:
                p["category"] = category
            all_posts.extend(posts)
            print(f"  → {len(posts)} posts above {MIN_LIKES} likes")

    # Sort by engagement
    all_posts.sort(key=lambda x: x["likes"], reverse=True)
    return all_posts


def filter_and_draft(posts):
    """Use Claude to filter for relevance and draft content suggestions."""
    if not ANTHROPIC_KEY:
        print("[WARN] No ANTHROPIC_API_KEY — returning raw posts")
        return posts

    import anthropic
    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

    posts_text = ""
    for i, p in enumerate(posts):
        caption = (p["caption"] or "")[:500]
        posts_text += f"\n---\nPOST {i+1} | @{p['username']} | {p['likes']} likes | {p['comments']} comments | {p['category']}\n{caption}\n"

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=4000,
        system="""You are Alice Bazdikian's content strategist. Alice is an AI Strategist & Educator who teaches entrepreneurs and small businesses how to use Claude as their business analyst.

Her brand voice: practical, no-jargon, Hormozi-style hooks, speaks to women solopreneurs and SMB leaders.
Her CTA: Book a free AI Diagnostic at smallbusinessaicoach.com

Review these Instagram posts from AI influencers. For each post worth adapting:

1. SCORE it 1-10 on relevance to Alice's audience (solopreneurs, women entrepreneurs, SMB leaders who want to use AI practically)
2. Write a one-line ANGLE — how Alice would adapt this to her niche
3. Write a HOOK — the first 2 lines of an Instagram caption in Alice's voice
4. Suggest FORMAT: carousel, quote post, or single image

Only include posts scoring 7+ relevance.
Output as JSON array: [{"post_number": 1, "original_account": "@username", "score": 9, "angle": "...", "hook": "...", "format": "carousel"}]""",
        messages=[{"role": "user", "content": f"Here are this week's top posts from AI accounts:\n{posts_text}"}],
    )

    # Parse Claude's response
    text = response.content[0].text
    try:
        # Find JSON in response
        start = text.index("[")
        end = text.rindex("]") + 1
        suggestions = json.loads(text[start:end])
    except (ValueError, json.JSONDecodeError):
        print("[WARN] Could not parse Claude's suggestions")
        suggestions = []

    # Merge suggestions with original post data
    for s in suggestions:
        idx = s.get("post_number", 0) - 1
        if 0 <= idx < len(posts):
            s["original_caption"] = (posts[idx]["caption"] or "")[:300]
            s["original_url"] = posts[idx]["url"]
            s["likes"] = posts[idx]["likes"]

    return suggestions


def format_digest_email(suggestions, all_posts):
    """Format suggestions as branded HTML email."""
    date_str = datetime.now().strftime("%B %d, %Y")
    total_scraped = len(all_posts)
    total_suggested = len(suggestions)

    rows = ""
    for i, s in enumerate(suggestions):
        rows += f"""
        <tr style="border-bottom:1px solid #e8e0d4;">
          <td style="padding:20px 16px;vertical-align:top;">
            <div style="font-family:'Inter',sans-serif;font-size:11px;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:#C9A847;margin-bottom:6px;">{s.get('format','carousel').upper()} · Score {s.get('score','?')}/10</div>
            <div style="font-family:'Playfair Display',serif;font-size:18px;font-weight:700;color:#1C1C1C;margin-bottom:8px;">{s.get('hook','')}</div>
            <div style="font-size:13px;color:#6B6560;margin-bottom:8px;line-height:1.6;"><strong>Angle:</strong> {s.get('angle','')}</div>
            <div style="font-size:12px;color:#999;">From {s.get('original_account','')} · {s.get('likes',0)} likes · <a href="{s.get('original_url','#')}" style="color:#7D2240;">View original</a></div>
          </td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet"></head>
<body style="margin:0;padding:0;background:#F7F3EE;font-family:'Inter',sans-serif;">
<div style="max-width:640px;margin:0 auto;padding:40px 24px;">

  <div style="text-align:center;margin-bottom:32px;">
    <div style="font-family:'Playfair Display',serif;font-size:28px;font-weight:700;color:#1C1C1C;">Weekly Content Scout</div>
    <div style="font-size:13px;color:#6B6560;margin-top:4px;">{date_str} · {total_scraped} posts scanned · {total_suggested} worth adapting</div>
  </div>

  <div style="background:#fff;border:1px solid #e8e0d4;border-radius:12px;overflow:hidden;">
    <div style="background:linear-gradient(135deg,#7D2240,#3d1022);padding:20px 24px;">
      <div style="font-family:'Inter',sans-serif;font-size:12px;font-weight:600;letter-spacing:0.12em;text-transform:uppercase;color:#C9A847;">This week's top content ideas</div>
      <div style="font-size:14px;color:rgba(255,255,255,0.7);margin-top:4px;">Reply with the numbers you want me to create (e.g. "1, 3, 5")</div>
    </div>
    <table style="width:100%;border-collapse:collapse;">
      {rows}
    </table>
  </div>

  <div style="text-align:center;margin-top:32px;font-size:12px;color:#999;">
    Scraped from 13 accounts across AI Automation, AI Tools, and Vibe Coding.<br>
    Auto-generated by your content pipeline · smallbusinessaicoach.com
  </div>

</div>
</body>
</html>"""

    return html


def save_results(suggestions, all_posts):
    """Save scout results locally."""
    date_str = datetime.now().strftime("%Y-%m-%d")
    out_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(out_dir, exist_ok=True)

    # Save raw posts
    with open(os.path.join(out_dir, f"scout-raw-{date_str}.json"), "w") as f:
        json.dump(all_posts, f, indent=2)

    # Save suggestions
    with open(os.path.join(out_dir, f"scout-suggestions-{date_str}.json"), "w") as f:
        json.dump(suggestions, f, indent=2)

    # Save email HTML
    html = format_digest_email(suggestions, all_posts)
    with open(os.path.join(out_dir, f"scout-digest-{date_str}.html"), "w") as f:
        f.write(html)

    return html


def send_digest(html):
    """Send the scout digest via Gmail."""
    try:
        from send_email import send_html_email
        msg_id = send_html_email(
            to=ALICE_EMAIL,
            subject=f"📡 Weekly Content Scout — {datetime.now().strftime('%b %d')}",
            html_body=html,
        )
        print(f"\n✓ Digest sent! Message ID: {msg_id}")
        return msg_id
    except Exception as e:
        print(f"\n[WARN] Could not send email: {e}")
        print("Digest saved locally — check output/ folder")
        return None


def main():
    print("=" * 60)
    print("WEEKLY INSTAGRAM CONTENT SCOUT")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"Accounts: {sum(len(v) for v in ACCOUNTS.values())}")
    print("=" * 60)

    # Step 1: Scrape
    all_posts = scrape_all()
    print(f"\nTotal posts scraped: {len(all_posts)}")

    if not all_posts:
        print("No posts found — check API token and network")
        return

    # Step 2: Filter & draft suggestions
    print("\nFiltering for relevance + drafting hooks...")
    suggestions = filter_and_draft(all_posts)
    print(f"Content suggestions: {len(suggestions)}")

    # Step 3: Save locally
    html = save_results(suggestions, all_posts)
    print(f"\nResults saved to output/")

    # Step 4: Send email digest
    send_digest(html)

    print("\n✓ Scout complete!")


if __name__ == "__main__":
    main()
