"""
Claude API integration for the Reddit Scout Agent.
Scores posts for engagement opportunity and drafts value-first replies.
"""

import json
import anthropic
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL
from reddit_scout_config import OPPORTUNITY_KEYWORDS

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SCORING_SYSTEM_PROMPT = f"""You are a Reddit engagement scout for Alice Bazdikian, an AI coach who helps small business owners (1-50 employees) adopt AI tools practically.

Your job: evaluate Reddit posts for engagement opportunity. Alice wants to reply to posts where she can provide genuine value and build authority as an AI expert for small businesses.

For each post, return a JSON object with:
- post_id: the post ID provided
- opportunity_type: one of "help_request", "pain_point", "lead", or "skip"
  - "help_request": someone asking how to use AI, what tools to pick, or how to automate something
  - "pain_point": someone frustrated with manual work, overwhelmed by AI options, or struggling with tech adoption
  - "lead": someone actively seeking an AI consultant, coach, trainer, or implementation partner
  - "skip": not relevant to Alice's expertise
- relevance_score: integer 1-10 (10 = perfect fit)
- reason: 1 sentence explaining the score

Scoring guidance:
- BOOST scores for: questions about AI for small business, people overwhelmed by AI tool options, anyone mentioning coaching/training needs, Shopify/e-commerce automation, workflow automation, hiring VAs vs using AI
- LOWER scores for: purely technical developer questions, enterprise-scale problems, crypto/trading bots, academic research, posts that are just sharing news with no question or pain point
- A post that's a direct question from an SMB owner about AI = score 8+
- A post venting about being overwhelmed by tech = score 6-7
- A general discussion with no clear engagement angle = score 3-4

Relevant keywords for context: {', '.join(OPPORTUNITY_KEYWORDS)}

Return ONLY a JSON array of objects. No markdown, no explanation."""

DRAFTING_SYSTEM_PROMPT = """You're writing a quick Reddit reply as Alice Bazdikian, an AI coach for small business owners. She's a real person — write like she's typing on her phone between meetings.

RULES:
- SHORT. 2-3 sentences max, maybe 4 if you really need to. This is Reddit, not a blog post.
- Colloquial. "honestly", "tbh", "I've seen this a ton", "game changer". No essay structure. No bullet points unless the person asked for a list.
- Lead with Claude. Alice's go-to tool is Claude (and Claude Cowork for team workflows). Default to recommending Claude for anything involving writing, email, customer support, SOPs, brainstorming, data analysis. Only mention other tools if Claude genuinely can't do it.
- DO NOT mention Zapier, Make.com, or other automation platforms. Alice's approach is Claude-first. If someone needs to connect apps, just say "you can layer in automation later" without naming tools.
- No "I'm an AI coach" opener. Just answer the question like someone who knows their stuff.
- Soft CTA only when it fits naturally — "happy to help if you want to dig into this more" or "DM me if you want the exact workflow I use". Skip it if it feels forced.
- NO LINKS. Reddit flags link-dropping.
- Sound like a person, not a ChatGPT response. Contractions, casual phrasing, occasional "lol" or "ngl" if the vibe fits.

Alice's background: She uses Claude daily to run her own business and coaches SMB owners on AI adoption. Her framework is the A.I.R. Method (Assess, Implement, Refine). She's big on Claude Cowork for ongoing business tasks and Claude Projects for organizing workflows."""


BATCH_SIZE = 20  # Score this many posts per Claude call


def score_posts(posts):
    """Score a batch of posts for engagement opportunity using Claude.

    Sends posts in batches to avoid response truncation.

    Args:
        posts: list of dicts with keys: post_id, title, body, subreddit

    Returns:
        list of dicts with keys: post_id, opportunity_type, relevance_score, reason
    """
    if not posts:
        return []

    all_scores = []

    for i in range(0, len(posts), BATCH_SIZE):
        batch = posts[i:i + BATCH_SIZE]
        posts_text = json.dumps([
            {
                "post_id": p["post_id"],
                "subreddit": p["subreddit"],
                "title": p["title"],
                "body": p.get("body", "")[:300],
            }
            for p in batch
        ], indent=2)

        try:
            response = client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=4096,
                system=SCORING_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": f"Score these Reddit posts:\n\n{posts_text}"}],
            )
            raw = response.content[0].text.strip()
            # Handle potential markdown wrapping
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            scores = json.loads(raw)
            all_scores.extend(scores)
            print(f"[Scout Scorer] Scored batch {i // BATCH_SIZE + 1}: {len(scores)} posts")
        except Exception as e:
            print(f"[Scout Scorer] ERROR scoring batch {i // BATCH_SIZE + 1}: {e}")
            continue

    print(f"[Scout Scorer] Total scored: {len(all_scores)} posts")
    return all_scores


def draft_reply(post, score_data):
    """Draft a value-first Reddit reply for a scored post.

    Args:
        post: dict with keys: title, body, subreddit, permalink
        score_data: dict with keys: opportunity_type, relevance_score, reason

    Returns:
        str: the draft reply text
    """
    context = (
        f"Subreddit: r/{post['subreddit']}\n"
        f"Post title: {post['title']}\n"
        f"Post body: {post.get('body', '(no body)')}\n"
        f"Opportunity type: {score_data['opportunity_type']}\n"
        f"Why this is relevant: {score_data['reason']}"
    )

    try:
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=512,
            system=DRAFTING_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": f"Draft a reply for this Reddit post:\n\n{context}"}],
        )
        reply = response.content[0].text.strip()
        print(f"[Scout Scorer] Drafted reply for: {post['title'][:50]}...")
        return reply
    except Exception as e:
        print(f"[Scout Scorer] ERROR drafting reply: {e}")
        return ""


if __name__ == "__main__":
    test_posts = [
        {
            "post_id": "test1",
            "subreddit": "smallbusiness",
            "title": "How can I use AI to handle my customer support emails?",
            "body": "I run a small e-commerce shop and I'm drowning in customer emails. Spending 3 hours a day just responding to the same questions over and over.",
        },
        {
            "post_id": "test2",
            "subreddit": "Shopify",
            "title": "Best apps for automating order fulfillment?",
            "body": "Looking for recommendations on Shopify apps that can automate my shipping and inventory management.",
        },
    ]
    scores = score_posts(test_posts)
    for s in scores:
        print(f"  [{s['relevance_score']}] {s['opportunity_type']}: {s['reason']}")
    if scores:
        reply = draft_reply(test_posts[0], scores[0])
        print(f"\nDraft reply:\n{reply}")
