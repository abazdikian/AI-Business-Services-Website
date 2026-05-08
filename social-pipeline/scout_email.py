"""
Email formatting for the Reddit Scout Agent.
Produces hot alert emails and morning summary digests.
"""

import html


BURGUNDY = "#7D2240"
GOLD = "#C9A847"
EGGSHELL = "#F7F3EE"
CHARCOAL = "#1C1C1C"
MUTED = "#6B6560"

OPPORTUNITY_LABELS = {
    "lead": {"label": "Lead", "color": BURGUNDY, "icon": "&#127919;"},
    "help_request": {"label": "Help Request", "color": GOLD, "icon": "&#10067;"},
    "pain_point": {"label": "Pain Point", "color": "#D4764E", "icon": "&#128161;"},
}


def _escape(text):
    return html.escape(text or "")


def _reply_box(draft_reply):
    """Render a draft reply in a copy-friendly box."""
    if not draft_reply:
        return ""
    return f"""
    <div style="background:#fff;border:1px solid #e0dcd7;border-radius:8px;padding:16px;margin:12px 0;font-family:Arial,sans-serif;font-size:14px;line-height:1.6;color:{CHARCOAL};white-space:pre-wrap;">{_escape(draft_reply)}</div>
    <p style="font-size:12px;color:{MUTED};margin:4px 0 0 0;">Copy the text above and paste into your Reddit reply</p>
    """


def format_hot_alert(post, score_data, draft_reply):
    """Format an immediate hot alert email for a single high-scoring post.

    Args:
        post: dict with title, subreddit, body, permalink, score, num_comments
        score_data: dict with opportunity_type, relevance_score, reason
        draft_reply: str, the drafted reply text

    Returns:
        tuple: (subject, html_body)
    """
    opp = OPPORTUNITY_LABELS.get(score_data["opportunity_type"], OPPORTUNITY_LABELS["help_request"])
    thread_url = f"https://www.reddit.com{post.get('permalink', '')}"
    title = _escape(post["title"])
    body_preview = _escape(post.get("body", "")[:300])

    subject = f"\U0001f525 Reddit Opportunity: {post['title'][:60]}"

    html_body = f"""
    <html>
    <body style="margin:0;padding:0;background:{EGGSHELL};font-family:Arial,sans-serif;">
    <div style="max-width:600px;margin:0 auto;padding:24px;">

        <!-- Header -->
        <div style="background:{BURGUNDY};border-radius:12px 12px 0 0;padding:20px 24px;">
            <h1 style="color:#fff;font-family:Georgia,serif;font-size:20px;margin:0;">
                {opp['icon']} Hot Reddit Opportunity
            </h1>
            <p style="color:rgba(255,255,255,0.8);font-size:13px;margin:6px 0 0 0;">
                Score: {score_data['relevance_score']}/10 &bull;
                r/{_escape(post['subreddit'])} &bull;
                {opp['label']}
            </p>
        </div>

        <!-- Content -->
        <div style="background:#fff;border-radius:0 0 12px 12px;padding:24px;border:1px solid #e0dcd7;border-top:none;">

            <h2 style="font-family:Georgia,serif;color:{CHARCOAL};font-size:18px;margin:0 0 8px 0;">
                <a href="{thread_url}" style="color:{CHARCOAL};text-decoration:none;">{title}</a>
            </h2>

            <p style="color:{MUTED};font-size:13px;margin:0 0 16px 0;">
                {post.get('score', 0)} upvotes &bull; {post.get('num_comments', 0)} comments &bull;
                {_escape(score_data.get('reason', ''))}
            </p>

            {f'<div style="background:{EGGSHELL};border-radius:8px;padding:14px;margin:0 0 16px 0;font-size:14px;color:{CHARCOAL};line-height:1.5;">{body_preview}</div>' if body_preview else ''}

            <h3 style="font-family:Georgia,serif;color:{BURGUNDY};font-size:15px;margin:20px 0 8px 0;">
                Your Draft Reply:
            </h3>
            {_reply_box(draft_reply)}

            <div style="text-align:center;margin:24px 0 8px 0;">
                <a href="{thread_url}" style="display:inline-block;background:{BURGUNDY};color:#fff;text-decoration:none;padding:12px 28px;border-radius:8px;font-weight:bold;font-size:14px;">
                    Open Thread &rarr;
                </a>
            </div>
        </div>

        <p style="text-align:center;color:{MUTED};font-size:11px;margin:16px 0 0 0;">
            Reddit Scout &bull; smallbusinessaicoach.com
        </p>
    </div>
    </body>
    </html>
    """

    return subject, html_body


def format_morning_summary(posts_with_replies):
    """Format the morning summary digest with all warm opportunities.

    Args:
        posts_with_replies: list of dicts, each with:
            - post: the post dict
            - score_data: the scoring dict
            - draft_reply: the drafted reply text

    Returns:
        tuple: (subject, html_body)
    """
    if not posts_with_replies:
        return None, None

    # Group by opportunity type
    grouped = {"lead": [], "help_request": [], "pain_point": []}
    for item in posts_with_replies:
        opp_type = item["score_data"]["opportunity_type"]
        if opp_type in grouped:
            grouped[opp_type].append(item)

    total = len(posts_with_replies)
    subject = f"\U0001f4cb Reddit Scout: {total} opportunities today"

    # Build sections
    sections_html = ""
    for opp_type, items in grouped.items():
        if not items:
            continue
        opp = OPPORTUNITY_LABELS[opp_type]
        items_html = ""
        for item in items:
            post = item["post"]
            score_data = item["score_data"]
            draft_reply = item["draft_reply"]
            thread_url = f"https://www.reddit.com{post.get('permalink', '')}"
            body_preview = _escape(post.get("body", "")[:200])

            items_html += f"""
            <div style="background:#fff;border:1px solid #e0dcd7;border-radius:10px;padding:18px;margin:0 0 14px 0;">
                <div style="display:flex;justify-content:space-between;align-items:center;margin:0 0 8px 0;">
                    <span style="font-size:12px;color:{MUTED};font-weight:bold;">r/{_escape(post['subreddit'])}</span>
                    <span style="background:{opp['color']};color:#fff;font-size:11px;padding:2px 8px;border-radius:12px;">
                        {score_data['relevance_score']}/10
                    </span>
                </div>
                <h3 style="font-family:Georgia,serif;color:{CHARCOAL};font-size:16px;margin:0 0 6px 0;">
                    <a href="{thread_url}" style="color:{CHARCOAL};text-decoration:none;">{_escape(post['title'])}</a>
                </h3>
                <p style="color:{MUTED};font-size:13px;margin:0 0 8px 0;">
                    {post.get('score', 0)} upvotes &bull; {post.get('num_comments', 0)} comments &bull;
                    {_escape(score_data.get('reason', ''))}
                </p>
                {f'<p style="font-size:13px;color:{CHARCOAL};line-height:1.5;margin:0 0 12px 0;">{body_preview}...</p>' if body_preview else ''}
                <details style="margin:8px 0 0 0;">
                    <summary style="cursor:pointer;color:{BURGUNDY};font-weight:bold;font-size:13px;">Show Draft Reply</summary>
                    {_reply_box(draft_reply)}
                </details>
            </div>
            """

        sections_html += f"""
        <div style="margin:0 0 28px 0;">
            <h2 style="font-family:Georgia,serif;color:{BURGUNDY};font-size:17px;margin:0 0 14px 0;">
                {opp['icon']} {opp['label']}s ({len(items)})
            </h2>
            {items_html}
        </div>
        """

    html_body = f"""
    <html>
    <body style="margin:0;padding:0;background:{EGGSHELL};font-family:Arial,sans-serif;">
    <div style="max-width:600px;margin:0 auto;padding:24px;">

        <!-- Header -->
        <div style="background:{BURGUNDY};border-radius:12px;padding:24px;margin:0 0 24px 0;">
            <h1 style="color:#fff;font-family:Georgia,serif;font-size:22px;margin:0;">
                &#128203; Reddit Scout — Morning Briefing
            </h1>
            <p style="color:rgba(255,255,255,0.8);font-size:14px;margin:8px 0 0 0;">
                {total} engagement opportunities found across 6 subreddits
            </p>
        </div>

        {sections_html}

        <p style="text-align:center;color:{MUTED};font-size:11px;margin:24px 0 0 0;">
            Reddit Scout &bull; smallbusinessaicoach.com
        </p>
    </div>
    </body>
    </html>
    """

    return subject, html_body


if __name__ == "__main__":
    # Quick test
    test_post = {
        "post_id": "test1",
        "title": "How do I use AI to handle customer support?",
        "subreddit": "smallbusiness",
        "body": "I run a small retail shop and I'm drowning in customer emails.",
        "permalink": "/r/smallbusiness/comments/test1/how_do_i_use_ai/",
        "score": 25,
        "num_comments": 8,
    }
    test_score = {
        "opportunity_type": "help_request",
        "relevance_score": 9,
        "reason": "SMB owner asking about AI for customer support — direct fit",
    }
    test_reply = "Great question! For handling repetitive customer emails, I'd start with something simple..."

    subj, body = format_hot_alert(test_post, test_score, test_reply)
    print(f"Subject: {subj}")
    print(f"HTML length: {len(body)} chars")

    subj2, body2 = format_morning_summary([
        {"post": test_post, "score_data": test_score, "draft_reply": test_reply}
    ])
    print(f"Summary subject: {subj2}")
    print(f"Summary HTML length: {len(body2)} chars")
