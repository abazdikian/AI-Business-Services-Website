"""
Render drafted posts into a branded HTML digest email.
"""

from datetime import datetime
from config import BRAND_NAME, WEBSITE_URL


CATEGORY_LABELS = {
    "ai-news": "AI News",
    "how-to": "How-To",
    "thought-leadership": "Hot Take",
    "engagement": "Engagement",
    "promo": "Your Business",
}

CATEGORY_COLORS = {
    "ai-news": "#7D2240",
    "how-to": "#C9A847",
    "thought-leadership": "#651B33",
    "engagement": "#6B6560",
    "promo": "#B8952E",
}


def format_email(items):
    """Render a list of drafted post items into a branded HTML email string."""
    date_str = datetime.now().strftime("%B %d, %Y")

    cards_html = ""
    for i, item in enumerate(items):
        cat = item.get("category", "ai-news")
        cat_label = CATEGORY_LABELS.get(cat, cat)
        cat_color = CATEGORY_COLORS.get(cat, "#7D2240")

        hashtags = item.get("hashtags", {})
        all_tags = hashtags.get("branded", []) + hashtags.get("niche", []) + hashtags.get("reach", [])
        tags_str = " ".join(all_tags)

        caption = item.get("caption", "")
        caption_html = caption.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")

        # Format repurposed content sections
        linkedin_text = item.get("linkedin_text", "")
        linkedin_html = linkedin_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>") if linkedin_text else ""

        twitter_thread = item.get("twitter_thread", [])
        thread_html = ""
        for t_i, tweet in enumerate(twitter_thread):
            tweet_escaped = tweet.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            thread_html += f'<p style="font-size:12px;color:#1C1C1C;line-height:1.5;margin:0 0 6px;padding-left:12px;border-left:2px solid rgba(201,168,71,0.3);"><strong style="color:#C9A847;">{t_i+1}/</strong> {tweet_escaped}</p>'

        quote_text = item.get("quote_text", "")
        video_script = item.get("video_script", "")
        video_html = video_script.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>") if video_script else ""

        # Build repurposed sections
        repurposed_html = ""
        if linkedin_html:
            repurposed_html += f'''
              <div style="margin-top:12px;padding:12px 16px;background:rgba(0,119,181,0.04);border-left:3px solid #0077B5;border-radius:0 8px 8px 0;">
                <p style="font-size:10px;font-weight:700;color:#0077B5;letter-spacing:0.08em;text-transform:uppercase;margin:0 0 6px;">LinkedIn Text Post</p>
                <p style="font-size:12px;color:#1C1C1C;line-height:1.55;margin:0;">{linkedin_html}</p>
              </div>'''
        if thread_html:
            repurposed_html += f'''
              <div style="margin-top:12px;padding:12px 16px;background:rgba(29,155,240,0.04);border-left:3px solid #1DA1F2;border-radius:0 8px 8px 0;">
                <p style="font-size:10px;font-weight:700;color:#1DA1F2;letter-spacing:0.08em;text-transform:uppercase;margin:0 0 6px;">X/Twitter Thread</p>
                {thread_html}
              </div>'''
        if quote_text:
            repurposed_html += f'''
              <div style="margin-top:12px;padding:14px 18px;background:#7D2240;border-radius:8px;text-align:center;">
                <p style="font-family:Georgia,'Playfair Display',serif;font-size:15px;font-weight:700;color:#F7F3EE;line-height:1.4;margin:0;font-style:italic;">"{quote_text}"</p>
              </div>'''
        if video_html:
            repurposed_html += f'''
              <div style="margin-top:12px;padding:12px 16px;background:rgba(107,101,96,0.06);border-left:3px solid #6B6560;border-radius:0 8px 8px 0;">
                <p style="font-size:10px;font-weight:700;color:#6B6560;letter-spacing:0.08em;text-transform:uppercase;margin:0 0 6px;">30-Sec Video Script</p>
                <p style="font-size:12px;color:#1C1C1C;line-height:1.55;margin:0;font-style:italic;">{video_html}</p>
              </div>'''

        cards_html += f"""
        <tr><td style="padding:0 0 24px 0;">
          <table width="100%" cellpadding="0" cellspacing="0" style="background:#FFFFFF;border-radius:12px;border:1px solid rgba(28,28,28,0.09);overflow:hidden;">
            <tr><td style="padding:24px 28px;">
              <span style="display:inline-block;background:{cat_color};color:#F7F3EE;font-size:11px;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;padding:4px 12px;border-radius:100px;margin-bottom:12px;">{cat_label}</span>
              <h2 style="font-family:Georgia,'Playfair Display',serif;font-size:20px;font-weight:700;color:#1C1C1C;margin:12px 0 8px;line-height:1.3;">#{i+1} — {item.get('headline', '')}</h2>
              <p style="font-size:14px;color:#6B6560;line-height:1.6;margin:0 0 16px;">{item.get('summary', '')}</p>
              <div style="background:rgba(125,34,64,0.04);border-left:3px solid #C9A847;border-radius:0 8px 8px 0;padding:14px 18px;margin:0 0 4px;">
                <p style="font-size:10px;font-weight:700;color:#C9A847;letter-spacing:0.08em;text-transform:uppercase;margin:0 0 6px;">Instagram / Facebook Caption</p>
                <p style="font-size:13px;color:#1C1C1C;line-height:1.65;margin:0;">{caption_html}</p>
              </div>
              {repurposed_html}
              <div style="margin-top:14px;padding-top:12px;border-top:1px solid rgba(28,28,28,0.06);">
                <p style="font-size:12px;color:#6B6560;margin:0 0 4px;">{tags_str}</p>
                <a href="{item.get('source_url', '#')}" style="font-size:12px;color:#7D2240;font-weight:600;text-decoration:none;">View source &rarr;</a>
              </div>
            </td></tr>
          </table>
        </td></tr>"""

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#F7F3EE;font-family:Arial,'Inter',sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#F7F3EE;">
    <tr><td align="center" style="padding:32px 16px;">
      <table width="100%" cellpadding="0" cellspacing="0" style="max-width:620px;">
        <tr><td style="text-align:center;padding:0 0 32px;">
          <p style="font-family:Georgia,'Playfair Display',serif;font-size:24px;font-weight:700;color:#7D2240;margin:0 0 4px;">AB</p>
          <h1 style="font-family:Georgia,'Playfair Display',serif;font-size:28px;font-weight:700;color:#1C1C1C;margin:0 0 6px;line-height:1.2;">Weekly AI Digest</h1>
          <p style="font-size:13px;color:#6B6560;margin:0;">{date_str} &middot; {len(items)} stories curated for you</p>
        </td></tr>
        <tr><td style="padding:0 0 24px;"><div style="height:2px;background:linear-gradient(90deg,#7D2240,#C9A847);border-radius:2px;"></div></td></tr>
        {cards_html}
        <tr><td style="text-align:center;padding:24px 0 0;border-top:1px solid rgba(28,28,28,0.09);">
          <p style="font-size:14px;color:#1C1C1C;font-weight:600;margin:0 0 4px;">Reply with your picks for the week</p>
          <p style="font-size:12px;color:#6B6560;margin:0 0 16px;">Just reply with the numbers (e.g., "1, 3, 5, 8") and I'll prep them.</p>
          <p style="font-size:11px;color:#b0a8a0;margin:0;">{BRAND_NAME} &middot; <a href="{WEBSITE_URL}" style="color:#7D2240;text-decoration:none;">{WEBSITE_URL}</a></p>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""

    return html


if __name__ == "__main__":
    import os
    from config import OUTPUT_DIR

    sample_items = [
        {
            "headline": "Claude Can Now Run Your Calendar",
            "summary": "Anthropic released Claude Connectors, letting Claude access Google Calendar, Slack, and Drive directly.",
            "caption": "Your AI just became your executive assistant.\n\nClaude can now:\n→ Read your calendar\n→ Send Slack messages\n→ Pull files from Drive\n\nThis changes everything for solopreneurs.",
            "hashtags": {"branded": ["#SmallBusinessAI"], "niche": ["#ClaudeAI"], "reach": ["#Entrepreneur"]},
            "source_url": "https://anthropic.com/news/example",
            "category": "ai-news",
        },
        {
            "headline": "Stop Using AI Like Google",
            "summary": "Most business owners treat AI as a search engine. Here's why that's wasting 90% of its potential.",
            "caption": "Everyone's using Claude wrong.\n\nThey type a question. Get an answer. Close the tab.\n\nThat's like hiring an employee and only asking them for directions.\n\nHere's what the top 1% do instead →",
            "hashtags": {"branded": ["#AliceAI"], "niche": ["#AIforBusiness"], "reach": ["#WomenInBusiness"]},
            "source_url": "https://reddit.com/r/ClaudeAI/example",
            "category": "thought-leadership",
        },
    ]

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    html = format_email(sample_items)
    output_path = os.path.join(OUTPUT_DIR, "test-digest.html")
    with open(output_path, "w") as f:
        f.write(html)
    print(f"[Format] Test digest written to {output_path} ({len(html)} bytes)")
