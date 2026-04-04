"""
Use Claude API to curate raw stories into 10-14 post-ready items
with Hormozi-style captions and hashtags.
"""

import json
import re
import anthropic
from config import (
    ANTHROPIC_API_KEY, CLAUDE_MODEL,
    TOTAL_ITEMS_MIN, TOTAL_ITEMS_MAX,
)

SYSTEM_PROMPT = """You are a social media content strategist for Alice Bazdikian, a small business AI coach.

Your job: take raw AI news stories and turn them into social media post drafts.

BRAND VOICE:
- Friendly + authoritative. Like a smart friend who happens to be an expert.
- Hormozi-style hooks: punchy, contrarian, numbers-driven opening lines.
- Target audience: small business owners, especially women.
- Never use jargon. Never hype. Never generic.
- Include specific numbers and actionable steps when possible.

CAPTION STRUCTURE:
1. Hook line (bold, attention-grabbing, Hormozi-style)
2. 3-5 value bullets using → arrows
3. One-line CTA (e.g., "Save this for later", "Which one are you using?", "Link in bio for the full guide")

CONTENT CATEGORIES — assign each item one of:
- "ai-news": Breaking AI news relevant to small business owners
- "how-to": Practical tip or tutorial derived from the news
- "thought-leadership": Hot take, contrarian angle, or industry insight
- "engagement": Poll question, discussion prompt, or "which would you choose?"
- "promo": Tie the news to Alice's coaching, workshops, or scorecard (website: smallbusinessaicoach.com)

HASHTAGS — for each post, provide:
- branded: pick 2-3 from ["#SmallBusinessAI", "#AliceAI", "#AICoach"]
- niche: pick 2-3 from ["#ClaudeAI", "#AIforBusiness", "#AIProductivity"]
- reach: pick 2-3 from ["#SmallBusiness", "#Entrepreneur", "#WomenInBusiness"]

OUTPUT FORMAT: Return valid JSON — an array of objects, each with:
{
  "headline": "short punchy headline",
  "summary": "2-3 sentence summary of the story",
  "caption": "the full social media caption",
  "hashtags": {"branded": [...], "niche": [...], "reach": [...]},
  "source_url": "original URL",
  "category": "one of the 5 categories"
}

Return EXACTLY between """ + str(TOTAL_ITEMS_MIN) + " and " + str(TOTAL_ITEMS_MAX) + """ items.
Prioritize the most interesting, actionable, and relevant stories for small business owners.
Skip stories that are too technical, too niche, or not relevant to the audience."""


def draft_posts(raw_stories):
    """Take raw stories and produce curated, draft-ready post items via Claude API."""
    if not ANTHROPIC_API_KEY:
        print("[ERROR] ANTHROPIC_API_KEY not set")
        return []

    stories_text = json.dumps(raw_stories, indent=2)
    user_message = f"Here are {len(raw_stories)} raw AI news stories from this week.\n\nCurate the best ones and draft social media posts for each.\n\nRAW STORIES:\n{stories_text}"

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    try:
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=8000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )

        response_text = response.content[0].text

        try:
            items = json.loads(response_text)
        except json.JSONDecodeError:
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                items = json.loads(json_match.group())
            else:
                print("[ERROR] Could not parse Claude response as JSON")
                print(response_text[:500])
                return []

        print(f"[Draft] Generated {len(items)} post drafts")
        return items

    except Exception as e:
        print(f"[ERROR] Claude API failed: {e}")
        return []


if __name__ == "__main__":
    sample = [
        {
            "source": "reddit/r/ClaudeAI",
            "title": "Claude Code now supports parallel sub-agents",
            "body": "You can dispatch multiple agents to work on different tasks simultaneously.",
            "url": "https://reddit.com/r/ClaudeAI/example",
            "score": 150,
            "comments": 45,
            "created": 0,
        },
        {
            "source": "anthropic-blog",
            "title": "Introducing Claude 4.5 Haiku",
            "body": "Our fastest model yet, now available to all users.",
            "url": "https://anthropic.com/news/claude-4-5-haiku",
            "score": 0,
            "comments": 0,
            "created": 0,
        },
    ]
    results = draft_posts(sample)
    for item in results:
        print(f"\n[{item.get('category')}] {item.get('headline')}")
        print(f"  Caption: {item.get('caption', '')[:100]}...")
