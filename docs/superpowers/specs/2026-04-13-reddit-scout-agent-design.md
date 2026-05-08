# Reddit Scout Agent — Design Spec

**Date:** 2026-04-13
**Status:** Draft
**Author:** Alice Bazdikian + Claude

## Context

Alice runs smallbusinessaicoach.com and coaches small business owners on AI adoption. She needs to build authority on Reddit by being one of the first to reply to relevant threads — people asking for AI help, venting about manual workflows, or actively looking for coaching/consulting.

The existing `social-pipeline/` already fetches Reddit posts for weekly content curation. This agent is different: it's an **engagement scout** that runs hourly, scores threads for reply opportunity, drafts value-first comments, and delivers them via email so Alice can post quickly.

## Requirements

1. **Hourly scanning** of 6 subreddits for new posts (during active hours)
2. **AI-powered scoring** — classify each post as help_request, pain_point, lead, or skip
3. **Two-tier delivery:**
   - **Hot alerts** (score ≥ 7, post < 2h old) → immediate email with draft reply
   - **Warm queue** (score ≥ 5) → batched into a morning summary
4. **Draft replies** in Alice's voice — value-first, Reddit-casual, soft CTA only when natural
5. **Deduplication** — never surface the same post twice
6. **No auto-posting** — Alice reviews and posts manually

## Subreddits

| Subreddit | Focus |
|-----------|-------|
| r/smallbusiness | Core audience — SMB owners |
| r/Solopreneur | Solo founders, 1-person ops |
| r/EntrepreneurRideAlong | Early-stage builders |
| r/startups | Startup founders, some overlap |
| r/AiForSmallBusiness | Direct niche match |
| r/Shopify | E-commerce SMBs (AI automation angle) |

## Architecture

### Data Flow — Hourly Cycle

```
FETCH (6 subs, /new endpoint, last 2h window)
  → DEDUPE (skip posts in seen_posts.json)
  → SCORE (Claude: opportunity_type + relevance 1-10)
  → CLASSIFY
      ├─ HOT (score ≥ 7, age < 2h) → DRAFT reply → SEND alert email
      └─ WARM (score ≥ 5) → save to warm_queue.json
  → SAVE (update seen_posts.json)
```

### Data Flow — Daily Summary (8am ET)

```
LOAD warm_queue.json
  → DRAFT replies for all queued posts
  → FORMAT branded HTML digest
  → SEND summary email
  → CLEAR warm_queue.json
```

### File Structure

```
social-pipeline/
├─ reddit_scout.py          # Main orchestrator — entry point for hourly + daily
├─ reddit_scout_config.py   # Subreddits, keywords, thresholds, active hours
├─ scout_scorer.py          # Claude API: scoring + reply drafting
├─ scout_email.py           # HTML email formatting (alerts + digest)
├─ scout_data/
│   ├─ seen_posts.json      # Processed post IDs (rolling 7-day TTL)
│   └─ warm_queue.json      # Posts queued for morning summary
```

### Reused Modules

| Module | From | Used For |
|--------|------|----------|
| `gmail_auth.py` | existing | OAuth for Gmail API |
| `send_email.py` | existing | Send emails via Gmail |
| `config.py` | existing | Brand colors, ALICE_EMAIL, shared constants |

## Module Details

### reddit_scout_config.py

```python
SCOUT_SUBREDDITS = [
    {"name": "smallbusiness", "url": "https://www.reddit.com/r/smallbusiness/new.json?limit=25"},
    {"name": "Solopreneur", "url": "https://www.reddit.com/r/Solopreneur/new.json?limit=25"},
    {"name": "EntrepreneurRideAlong", "url": "https://www.reddit.com/r/EntrepreneurRideAlong/new.json?limit=25"},
    {"name": "startups", "url": "https://www.reddit.com/r/startups/new.json?limit=25"},
    {"name": "AiForSmallBusiness", "url": "https://www.reddit.com/r/AiForSmallBusiness/new.json?limit=25"},
    {"name": "Shopify", "url": "https://www.reddit.com/r/Shopify/new.json?limit=25"},
]

# Scoring thresholds
HOT_THRESHOLD = 7        # Score ≥ 7 + fresh → instant alert
WARM_THRESHOLD = 5        # Score ≥ 5 → morning summary
MAX_POST_AGE_HOURS = 2    # Only alert on posts < 2h old for HOT
SEEN_POSTS_TTL_DAYS = 7   # Purge seen posts older than 7 days

# Active hours (ET) — only scan during these hours
ACTIVE_HOURS_START = 7    # 7am ET
ACTIVE_HOURS_END = 22     # 10pm ET

# Keywords that boost scoring (used in Claude prompt as context)
OPPORTUNITY_KEYWORDS = [
    "AI automation", "automate", "AI tools", "ChatGPT for business",
    "Claude for business", "need help with AI", "AI consultant",
    "AI coach", "overwhelmed", "too many tools", "manual process",
    "AI training", "AI workshop", "implement AI", "AI strategy",
    "small business AI", "AI for my business"
]
```

### reddit_scout.py — Main Orchestrator

**Entry point with two modes:**
- `python reddit_scout.py hourly` — run the hourly scan cycle
- `python reddit_scout.py summary` — run the morning summary

**Hourly cycle:**
1. Check if within active hours — exit early if not
2. Fetch /new from each subreddit (public JSON API, same pattern as `fetch_reddit.py`). Filter by `created_utc` to only keep posts from the last 2 hours.
3. Filter out posts already in `seen_posts.json`
4. If no new posts, exit
5. Send batch to `scout_scorer.py` for scoring
6. Split results into HOT and WARM
7. For HOT posts: draft replies immediately, send one alert email per hot post (so Alice sees them as separate inbox items she can act on individually)
8. For WARM posts: append to `warm_queue.json`
9. Add all post IDs to `seen_posts.json` with timestamp
10. Purge seen posts older than 7 days

**Summary cycle:**
1. Load `warm_queue.json`
2. If empty, skip
3. Draft replies for all queued posts
4. Format into branded HTML digest
5. Send via Gmail
6. Clear the queue

### scout_scorer.py — Claude API Integration

**Two functions:**

`score_posts(posts: list) -> list[ScoredPost]`
- Sends all posts to Claude in a single batch call
- System prompt establishes Alice's niche, target audience, opportunity types
- Returns structured JSON: `{post_id, opportunity_type, relevance_score, reason}`
- Model: `claude-haiku-4-5-20251001` (fast, cheap — scoring is a classification task)

`draft_reply(post: dict, score_data: dict) -> str`
- Sends individual post + score context to Claude
- System prompt includes:
  - Alice's expertise and voice
  - Reddit reply best practices (no link-dropping, conversational tone)
  - Value-first framework: lead with advice, soft CTA only when natural
  - Reply length: 2-4 short paragraphs
- Model: `claude-haiku-4-5-20251001` (same model, consistent with existing pipeline)

**Scoring system prompt (summary):**
```
You are a Reddit engagement scout for Alice Bazdikian, an AI coach
who helps small business owners (1-50 employees) adopt AI tools
practically. Your job: evaluate Reddit posts for engagement opportunity.

Rate each post:
- opportunity_type: "help_request" (asking how to use AI), "pain_point"
  (frustrated with manual work or AI confusion), "lead" (actively
  seeking consultant/coach/training), or "skip" (not relevant)
- relevance_score: 1-10 (10 = perfect fit for Alice's expertise)
- reason: 1 sentence explaining the score

Boost scores for: questions about AI for small business, people
overwhelmed by AI tool options, anyone mentioning coaching/training
needs, Shopify/e-commerce automation questions.

Lower scores for: purely technical developer questions, enterprise-scale
problems, crypto/trading bots, academic research.
```

**Reply drafting system prompt (summary):**
```
You are drafting a Reddit reply for Alice Bazdikian, an AI coach for
small business owners. Write a reply that:

1. LEADS WITH VALUE — give specific, actionable advice first
2. SHOWS EXPERTISE — reference real AI tools, workflows, or frameworks
3. MATCHES REDDIT TONE — conversational, no corporate jargon, use "I"
4. SOFT CTA (only when natural) — e.g., "I work with SMBs on exactly
   this kind of thing — happy to share more if helpful"
5. NO LINKS — never include URLs in the reply (Reddit flags this)
6. LENGTH — 2-4 short paragraphs, not a wall of text

Alice's areas of expertise: AI automation for daily operations, Claude
and ChatGPT for business workflows, the A.I.R. Method (Assess,
Implement, Refine), training teams on AI adoption.
```

### scout_email.py — Email Formatting

**Two email types:**

**Hot Alert Email:**
- Subject: `🔥 Reddit Opportunity: [thread title truncated]`
- Body: Thread title (linked), subreddit, post body preview, opportunity type badge, draft reply (in a copy-friendly box), direct link to thread
- Minimal styling — speed over beauty

**Morning Summary Email:**
- Subject: `📋 Reddit Scout: [N] opportunities from yesterday`
- Branded HTML using existing brand colors (burgundy #7D2240, gold #C9A847, eggshell #F7F3EE)
- Sections grouped by opportunity type:
  - 🎯 Leads (actively seeking help)
  - ❓ Help Requests (asking AI questions)
  - 💡 Pain Points (frustrated, need solutions)
- Each entry: thread title (linked), subreddit tag, relevance score, post excerpt, draft reply

## Data Persistence

### seen_posts.json
```json
{
  "abc123": {"seen_at": "2026-04-13T08:00:00", "subreddit": "smallbusiness"},
  "def456": {"seen_at": "2026-04-13T09:00:00", "subreddit": "Shopify"}
}
```
Rolling window: entries older than 7 days are purged each run.

### warm_queue.json
```json
[
  {
    "post_id": "abc123",
    "title": "How do I use AI to handle customer emails?",
    "subreddit": "smallbusiness",
    "body": "I run a small retail shop and...",
    "permalink": "/r/smallbusiness/comments/abc123/...",
    "score": 15,
    "num_comments": 3,
    "created_utc": 1712900000,
    "opportunity_type": "help_request",
    "relevance_score": 6,
    "reason": "SMB owner asking about AI for email — direct fit"
  }
]
```
Cleared after the morning summary is sent.

## Scheduling

The script needs to run hourly during active hours and once at 8am for the summary.

**Option: System cron (launchd on macOS)**
```bash
# Hourly scan: every hour from 7am-10pm ET
0 7-22 * * * cd /Users/alicebazidian/Desktop/AI\ Project/AI\ Services\ Website && python3 social-pipeline/reddit_scout.py hourly

# Morning summary: 8am ET daily
0 8 * * * cd /Users/alicebazidian/Desktop/AI\ Project/AI\ Services\ Website && python3 social-pipeline/reddit_scout.py summary
```

**Note:** This only works when the Mac is running. For always-on operation, a future upgrade could move to a cloud scheduler (GitHub Actions, Vercel cron, etc.).

## Error Handling

- **Reddit API down/rate-limited:** Log warning, skip that subreddit, continue with others. Retry on next hourly cycle.
- **Claude API failure:** Log error, skip scoring for this cycle. Posts will be re-fetched next cycle (not yet in seen_posts.json since they weren't processed).
- **Gmail API failure:** Log error, save unsent emails to `scout_data/unsent/` as HTML files for manual review.
- **Empty results:** Normal — not every hour has new relevant posts. Exit silently.
- **Logging:** All output goes to stdout/stderr for cron log capture. Each run logs: subreddits checked, posts found, posts scored, hot/warm counts, emails sent.

## API Cost Estimate

- **Reddit:** Free (public JSON API, ~6 requests/hour = ~96/day)
- **Claude (scoring):** ~$0.01-0.05/day (Haiku, small batches, classification task)
- **Claude (drafting):** ~$0.02-0.10/day (Haiku, 5-15 replies/day avg)
- **Gmail API:** Free (well within quota)
- **Total:** ~$0.03-0.15/day, under $5/month

## Future Upgrades (Not In Scope)

- PRAW integration for comment-level scanning
- Auto-posting via Reddit API
- Engagement tracking (did the reply get upvotes?)
- A/B testing different reply styles
- Dashboard for browsing opportunity history

## Verification Plan

1. Run `reddit_scout.py hourly` manually and verify it fetches, scores, and sends an alert email
2. Run `reddit_scout.py summary` manually and verify the morning digest email
3. Run twice — verify deduplication works (no repeat posts)
4. Test outside active hours — verify it exits early
5. Test with no relevant posts — verify it handles empty results gracefully
6. Set up cron and verify it runs automatically for 24h
