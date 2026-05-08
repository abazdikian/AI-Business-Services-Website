# Content Sourcing Pipeline — Design Spec

## Overview

An automated weekly pipeline that fetches AI news from multiple sources, drafts social media post content with Hormozi-style hooks, formats a branded HTML digest email, and sends it to Alice's Gmail every Sunday at 9am ET via Claude Code scheduled trigger.

## Pipeline Flow

```
Sunday 9am ET — Scheduled Trigger
    │
    ├── 1. FETCH: Reddit (r/ClaudeAI, r/anthropic top posts)
    ├── 2. FETCH: Anthropic blog (new posts since last run)
    └── 3. FETCH: AI news via web search (trending AI + small biz stories)
    │
    ▼
    4. DEDUPE: Remove duplicate/overlapping stories
    │
    ▼
    5. DRAFT: Claude API generates 10-14 post-ready items
       - Headline
       - 2-3 sentence summary
       - Draft social caption (Hormozi-style, friendly + authoritative)
       - Hashtags (3 tiers: branded, niche, reach)
       - Source link
       - Content category label
    │
    ▼
    6. FORMAT: Render branded HTML email digest
    │
    ▼
    7. SEND: Gmail API → alice.b@alprosolutions.ca
```

## Content Sources

### Reddit (Public JSON API — no key needed)
- `https://www.reddit.com/r/ClaudeAI/top.json?t=week&limit=25`
- `https://www.reddit.com/r/anthropic/top.json?t=week&limit=25`
- Extract: title, selftext, url, score, num_comments, created_utc
- Filter: minimum score threshold (>10 upvotes) to skip noise

### Anthropic Blog
- Fetch `https://www.anthropic.com/news` or `/blog` page
- Extract: post titles, URLs, publish dates
- Filter: only posts from the last 7 days

### AI News (RSS + Direct Fetch)
- Fetch headlines from known AI news sources:
  - TechCrunch AI: `https://techcrunch.com/category/artificial-intelligence/feed/`
  - The Verge AI: `https://www.theverge.com/rss/ai-artificial-intelligence/index.xml`
  - MIT Technology Review AI: `https://www.technologyreview.com/feed/`
- Extract: titles, URLs, publish dates, descriptions
- Filter: only items from last 7 days, deduplicate against Reddit/Anthropic results
- Focus on stories relevant to small business / entrepreneurs (Claude API handles relevance filtering in the drafting step)

## Content Drafting (Claude API)

### Input
Raw stories from all sources (typically 30-50 raw items after deduplication).

### Output
10-14 curated items, each with:

```json
{
  "headline": "Claude Can Now Run Your Calendar",
  "summary": "Anthropic released Claude Connectors this week, letting Claude access Google Calendar, Slack, and Drive directly. This means small business owners can now...",
  "caption": "Your AI just became your executive assistant.\n\nClaude can now:\n→ Read your calendar\n→ Send Slack messages\n→ Pull files from Drive\n\nNo API keys. No setup. Just connect and go.\n\nThis changes everything for solopreneurs who waste 12+ hours/week on admin.\n\nHere's how to set it up (thread) 👇",
  "hashtags": {
    "branded": ["#SmallBusinessAI", "#AliceAI", "#AICoach"],
    "niche": ["#ClaudeAI", "#AIforBusiness", "#AIProductivity"],
    "reach": ["#SmallBusiness", "#Entrepreneur", "#WomenInBusiness"]
  },
  "source_url": "https://www.anthropic.com/news/claude-connectors",
  "category": "ai-news"
}
```

### Content Categories (target mix per digest)
- `ai-news` — 4-5 items (Reddit + Anthropic blog + web search)
- `how-to` — 2-3 items (practical tips derived from news or evergreen)
- `thought-leadership` — 2-3 items (hot takes, contrarian angles)
- `engagement` — 1-2 items (poll/question ideas derived from trending topics)
- `promo` — 1 item (tie current news to Alice's workshops/coaching)

### Drafting Prompt
The Claude API call uses a system prompt that includes:
- Brand voice: friendly + authoritative, Hormozi-style hooks
- Target audience: small business owners, especially women
- Caption structure: hook line → value bullets → CTA
- Avoid: jargon, hype, generic advice
- Include: specific numbers, actionable steps, relatable scenarios

### Caption Style Examples
- "Your team is wasting 12 hours/week on tasks AI does in minutes"
- "Stop Googling. Start building AI systems."
- "I automated 80% of my admin. Here's the exact setup."
- "Everyone's using Claude wrong. Here's what the top 1% do differently."

## Email Format

### HTML Digest Structure
```
┌─────────────────────────────┐
│  AB logo + "Weekly AI Digest"│
│  Date: April 6, 2026        │
├─────────────────────────────┤
│                              │
│  [Category Badge] AI NEWS    │
│  ─── Headline ───           │
│  Summary text...             │
│                              │
│  📱 Draft Caption:           │
│  "Your AI just became..."    │
│                              │
│  #hashtags #listed #here     │
│  🔗 Source link              │
│                              │
│  ─────────────────────────── │
│  (repeat for 10-14 items)    │
│                              │
├─────────────────────────────┤
│  Footer: smallbusinessai...  │
│  "Reply to this email with   │
│   your picks for the week"   │
└─────────────────────────────┘
```

### Brand Styling
- Background: `#F7F3EE` (eggshell)
- Card backgrounds: `#FFFFFF`
- Headlines: Playfair Display (fallback: Georgia, serif)
- Body: Inter (fallback: Arial, sans-serif)
- Category badges: burgundy `#7D2240` bg, white text, rounded pill
- Accent borders: gold `#C9A847`
- Links: burgundy `#7D2240`
- Muted text: `#6B6560`

## Technical Implementation

### Language
Python — to reuse existing Gmail API OAuth setup from `/Users/alicebazidian/Desktop/AL Pro Solar Sales Funnel/`.

### File Structure
All files live in a new directory: `social-pipeline/`

```
social-pipeline/
├── fetch_reddit.py        # Fetch top posts from r/ClaudeAI + r/anthropic
├── fetch_anthropic.py     # Fetch recent Anthropic blog posts
├── fetch_news.py          # Web search for AI + small biz news
├── draft_posts.py         # Claude API drafts captions + hashtags
├── format_email.py        # Render branded HTML digest
├── send_email.py          # Gmail API send (reuses AL Pro auth pattern)
├── run_pipeline.py        # Orchestrator — runs all steps in sequence
├── gmail_auth.py          # Copied/adapted from AL Pro project
├── config.py              # Constants: email, API keys, thresholds
├── last_run.json          # Timestamp of last run (for "since last week" filtering)
└── requirements.txt       # Python dependencies
```

### Gmail Auth (Remote Trigger Compatibility)
The `gmail_auth.py` module supports two credential sources:
1. **Local files** — `credentials.json` + `token.json` (for local dev/testing)
2. **Environment variables** — `GMAIL_CREDENTIALS_JSON` + `GMAIL_TOKEN_JSON` (for remote scheduled trigger)

```python
# Pseudocode for dual-source auth
if os.environ.get('GMAIL_TOKEN_JSON'):
    # Write env var contents to temp files, use those
    token_data = os.environ['GMAIL_TOKEN_JSON']
    creds = Credentials.from_authorized_user_info(json.loads(token_data), SCOPES)
else:
    # Use local files (existing pattern)
    creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
```

### Dependencies
- `google-auth`, `google-auth-oauthlib`, `google-api-python-client` — Gmail API
- `anthropic` — Claude API for drafting
- `requests` — HTTP fetches for Reddit/Anthropic blog
- No web scraping libraries needed — Reddit has a public JSON API, Anthropic blog is HTML parseable with basic requests + string parsing

### API Keys Required
- `ANTHROPIC_API_KEY` — for Claude API drafting
- Gmail OAuth credentials — `credentials.json` + `token.json` (already exist)
- No Reddit API key needed (public JSON endpoints)

### Scheduled Trigger
Claude Code remote trigger, configured via the `schedule` skill:
- **Schedule:** Every Sunday at 9:00 AM ET
- **Command:** `cd social-pipeline && python3 run_pipeline.py`
- **Environment:** Must include `ANTHROPIC_API_KEY`, `GMAIL_CREDENTIALS_JSON`, `GMAIL_TOKEN_JSON`

### Error Handling
- If a source fails (e.g., Reddit is down), log the error and continue with remaining sources
- If fewer than 5 items are sourced, the pipeline still runs but adds a note in the email: "Light news week — fewer items than usual"
- If Claude API fails, send the raw stories without drafted captions
- If Gmail send fails, save the HTML digest to `social-pipeline/output/digest-YYYY-MM-DD.html` as a local fallback

### State Management
- `last_run.json` stores the timestamp of the last successful run
- Used to filter "new since last run" for Anthropic blog posts
- Updated after successful email send

## Success Criteria
- Pipeline runs end-to-end without manual intervention
- 10-14 curated items per digest with draft captions and hashtags
- Branded HTML email lands in alice.b@alprosolutions.ca inbox every Sunday at 9am ET
- Each item has a clear category label, source link, and post-ready caption
- Captions use Hormozi-style hooks matching Alice's brand voice
