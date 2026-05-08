# Content Hub

Local web dashboard (http://localhost:4000) that pulls top competitor posts
from YouTube / LinkedIn / TikTok / Instagram / Facebook each Friday at 8am,
lets Alice pick which to repurpose, then queues an async "Create" job.

Spec: `.claude/plans/use-the-brand-assets-ai-jolly-meerkat.md`

## Install

```bash
cd "AI Services Website"
python3 -m venv .venv && source .venv/bin/activate
pip install -r content_hub/requirements.txt
```

Set env vars (or add to `.env`):

```
APIFY_TOKEN=apify_api_xxx
ANTHROPIC_API_KEY=sk-ant-xxx
```

## Run

Seed fixture data so you can click around without hitting Apify:

```bash
python -m content_hub.scheduler --fixtures
```

Start the dashboard:

```bash
uvicorn content_hub.app:app --port 4000 --reload
```

Open: http://localhost:4000

Start the worker in another terminal so "Create" batches move from queued → done:

```bash
python -m content_hub.jobs.create_worker
```

## Weekly live pull

```bash
python -m content_hub.scheduler            # live Apify pull, writes week
python -m content_hub.scheduler --dry-run  # fetch, don't write
python -m content_hub.scheduler --skip-llm # skip Claude why-trending calls
```

## Friday 8am cron (launchd)

```bash
cp content_hub/com.alice.contenthub.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.alice.contenthub.plist
launchctl start com.alice.contenthub   # run now to smoke-test
```

`launchd` catches up on the next wake if the Mac is asleep at the scheduled time.

## Layout

```
content_hub/
├── app.py              FastAPI routes + HTMX endpoints
├── scheduler.py        Weekly Apify pull (cron entrypoint)
├── db.py               SQLite schema + queries
├── config.py           env + creators + hashtags + actor IDs
├── fetchers/           1 module per channel, normalized Post output
├── enrich/             format tag, hook, engagement rate, Haiku why-trending
├── jobs/create_worker  Stub that moves jobs queued → done
├── templates/          Jinja + HTMX
├── static/style.css    Burgundy / gold / eggshell brand
└── fixtures/           sample_week.json for offline demo
```

## Weekly process (Friday 8am)

Run in this order:
```bash
# Step 1 — Apify pull (fast, no LLM enrichment)
content_hub/run.sh
# This does: --skip-llm then --reparse automatically

# Step 2 — Start the worker (picks up queued Create jobs)
python -m content_hub.jobs.create_worker

# Step 3 — Start the reply monitor (fires render after approval)
# (to be wired into run.sh)
```

The launchd plist (`com.alice.contenthub.plist`) runs `content_hub/run.sh` every Friday at 8am.

## Content rules (source of truth: Brand Assets/AI Services Content Marketing plan.docx)

### Drafter rules
- **Slide 1 hook**: Always adapted from the source post's hook_line or title. Never invented.
- **Structure**: Five-Beat Story Structure — Hook → Problem → Solution → Proof → CTA
- **Slide titles**: 3-8 words, punchy, NOT descriptive labels
- **Caption first sentence**: Must match the energy of Slide 1 hook
- **CTA**: Must use one of the Active CTAs (rotate):
  1. Subscribe to newsletter → smallbusinessaicoach.com
  2. DM me the word DIAGNOSTIC
  3. Register for the next masterclass → smallbusinessaicoach.com
  4. Follow for weekly AI strategies for small business
  5. Comment [WORD] and I'll DM you [lead magnet]
- **TikTok templates**: Listicle, Negative, Tutorial, Breaking News — pick one per post
- **No invented hooks**, no generic titles, no descriptive labels

### Approval workflow
1. Alice selects posts in the hub → clicks "Create batch" → job queued
2. Worker drafts text only (post.md + caption.md) → uploads to Drive → sends approval email
3. Alice reviews and edits text **in Drive** before approving
4. Alice clicks "Approve & Render" at `/drafts/{job_id}` in the hub
5. Render runs: slides → PNGs → MP4 (TikTok) or PDF (LinkedIn) → uploaded to Drive

### Email rules
- Approval email contains: post title, inspired-by credit, Drive folder link only
- No file attachments, no caption preview, no individual file links
- Alice edits files directly in Drive before approving

### Python runtime
- Always use `content_hub/venv/bin/python` (Python 3.12)
- System python3 is 3.9 — too old, will crash on `str | None` syntax
