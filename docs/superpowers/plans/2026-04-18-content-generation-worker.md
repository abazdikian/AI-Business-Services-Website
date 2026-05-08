# Content Generation Worker Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the stub `content_hub/jobs/create_worker.py` into the end-to-end pipeline that drafts Alice-voice content per selected post, renders final files per channel, uploads to Drive, emails an approval digest, and re-renders to `/READY-TO-POST/` after Alice replies "Done."

**Architecture:** New modules under `content_hub/generate/`, `content_hub/render/`, `content_hub/drive/`, `content_hub/email_digest/`. Orchestrator in `create_worker.py` composes them. Reuses `social-pipeline/` for Gmail auth/send, Drive client, and carousel HTML templates. Voice profile is extracted once from `voice_samples/alice_posts.md` into a versioned YAML the drafter reads at boot.

**Tech Stack:** Python 3.12, FastAPI + HTMX (existing dashboard), Anthropic SDK (Claude Sonnet 4.6 for drafts, Haiku for why-trending), google-api-python-client (Slides + Drive), Playwright (carousel JPGs), ffmpeg-python (carousel MP4), Jinja2 (email HTML), pytest.

---

## File structure

**New files:**
```
content_hub/
  generate/__init__.py
  generate/voice.py                  Loads/rebuilds voice profile
  generate/draft.py                  Per-channel drafter (Claude Sonnet)
  generate/fingerprint.py            Topic-fingerprint dedupe for social
  generate/captions.py               CTA round-robin + hashtag composer
  generate/models.py                 Draft / SlideContent dataclasses
  render/__init__.py
  render/carousel_jpg.py             HTML → Playwright → JPG
  render/carousel_video.py           JPGs → MP4 via ffmpeg
  render/linkedin_pdf.py             HTML → Playwright → PDF
  render/yt_slides.py                Google Slides API deck creator
  drive/__init__.py
  drive/client.py                    get_service() wrapper
  drive/layout.py                    Week folder + SUMMARY.md writer
  drive/watch.py                     Pull edited drafts for re-render
  email_digest/__init__.py
  email_digest/render.py             Jinja HTML digest
  email_digest/send.py               Gmail send wrapper
  email_digest/reply_parser.py       Strict "Done" parser
  email_digest/templates/digest.html Jinja template
  voice_samples/voice_profile.yaml   Generated, checked in
  jobs/orchestrator.py               New: pipeline logic separated from worker loop
tests/content_hub/
  test_voice.py
  test_draft.py
  test_fingerprint.py
  test_captions.py
  test_carousel_jpg.py
  test_carousel_video.py
  test_linkedin_pdf.py
  test_yt_slides.py
  test_drive_layout.py
  test_email_digest.py
  test_reply_parser.py
  test_orchestrator.py
  fixtures/
    sample_posts.json                Fixture selected posts for end-to-end tests
```

**Modified files:**
- `content_hub/config.py` — add `DRAFTER_MODEL`, `DRIVE_ROOT_FOLDER_ID`, `CAPTION_LIMITS`.
- `content_hub/jobs/create_worker.py` — replace `handle()` stub with call to `orchestrator.run_job()`.
- `content_hub/app.py` — merge IG + TT into a single `social` channel tab.
- `content_hub/templates/week.html` — reflect new channel list.
- `content_hub/scheduler.py` — when writing posts, tag `channel='social'` for IG + TT and keep original in `raw` for fingerprinting.
- `content_hub/requirements.txt` — add deps.

---

## Task 1: Scaffold directories, deps, config additions

**Files:**
- Create (empty `__init__.py`): `content_hub/generate/__init__.py`, `content_hub/render/__init__.py`, `content_hub/drive/__init__.py`, `content_hub/email_digest/__init__.py`, `tests/content_hub/__init__.py`, `tests/content_hub/fixtures/__init__.py`
- Modify: `content_hub/requirements.txt`
- Modify: `content_hub/config.py`

- [ ] **Step 1.1: Create empty package directories + `__init__.py` files**

```bash
mkdir -p content_hub/{generate,render,drive,email_digest/templates} tests/content_hub/fixtures
for d in content_hub/generate content_hub/render content_hub/drive content_hub/email_digest tests/content_hub tests/content_hub/fixtures; do touch "$d/__init__.py"; done
```

- [ ] **Step 1.2: Add deps to `content_hub/requirements.txt`**

Append (keep existing lines):

```
anthropic>=0.40
google-api-python-client>=2.120
google-auth-httplib2>=0.2
google-auth-oauthlib>=1.2
playwright>=1.45
ffmpeg-python>=0.2
PyYAML>=6.0
pytest>=8
```

- [ ] **Step 1.3: Install + Playwright browsers**

```bash
source .venv-hub/bin/activate
pip install -r content_hub/requirements.txt
python -m playwright install chromium
```
Expected: chromium downloaded, no errors.

- [ ] **Step 1.4: Extend `content_hub/config.py`**

Append to the existing config.py (after the existing constants):

```python
DRAFTER_MODEL = "claude-sonnet-4-6"
DRIVE_ROOT_FOLDER_ID = os.environ.get("CONTENT_HUB_DRIVE_FOLDER_ID", "")
CAPTION_LIMITS = {"linkedin": 220, "social": 150, "youtube": 250}
SLIDES_PER_CAROUSEL = {"social": 8, "linkedin": 10}
VOICE_PROFILE_PATH = BASE_DIR / "voice_samples" / "voice_profile.yaml"
VOICE_SAMPLES_PATH = BASE_DIR / "voice_samples" / "alice_posts.md"
```

- [ ] **Step 1.5: Commit**

```bash
git add content_hub/ tests/ && git commit -m "chore: scaffold generate/render/drive/email_digest packages + deps"
```

---

## Task 2: Draft + SlideContent dataclasses

**Files:**
- Create: `content_hub/generate/models.py`
- Create: `tests/content_hub/test_models.py`

- [ ] **Step 2.1: Write the failing test**

`tests/content_hub/test_models.py`:

```python
from content_hub.generate.models import Draft, SlideContent

def test_draft_roundtrip():
    d = Draft(
        source_post_id="li_1",
        channel="linkedin",
        register="A",
        hook="Claude isn't a chatbot. It's a strategist.",
        slides=[SlideContent(kind="cover", title="Hook", body="Body")],
        caption="Body...",
        cta="book_diagnostic",
        hashtags=["#AIStrategy", "#AICoach"],
    )
    r = d.to_dict()
    back = Draft.from_dict(r)
    assert back == d
    assert back.slides[0].kind == "cover"
```

- [ ] **Step 2.2: Run to confirm FAIL**

```bash
pytest tests/content_hub/test_models.py -v
```
Expected: `ModuleNotFoundError: content_hub.generate.models`.

- [ ] **Step 2.3: Implement `content_hub/generate/models.py`**

```python
from dataclasses import dataclass, asdict, field

@dataclass
class SlideContent:
    kind: str       # 'cover' | 'content' | 'cta'
    title: str = ""
    body: str = ""

@dataclass
class Draft:
    source_post_id: str
    channel: str          # 'youtube' | 'linkedin' | 'social'
    register: str         # 'A' (long) | 'B' (short casual)
    hook: str
    slides: list[SlideContent] = field(default_factory=list)
    caption: str = ""
    cta: str = ""
    hashtags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Draft":
        slides = [SlideContent(**s) for s in d.get("slides", [])]
        return cls(**{**d, "slides": slides})
```

- [ ] **Step 2.4: PASS + commit**

```bash
pytest tests/content_hub/test_models.py -v && git add -A && git commit -m "feat(generate): Draft + SlideContent dataclasses"
```

---

## Task 3: Voice profile extraction (`generate/voice.py`)

**Files:**
- Create: `content_hub/generate/voice.py`
- Create: `tests/content_hub/test_voice.py`
- Create: `content_hub/voice_samples/voice_profile.yaml` (generated in step 3.5)

- [ ] **Step 3.1: Write the failing test**

`tests/content_hub/test_voice.py`:

```python
from content_hub.generate.voice import load_profile, build_system_prompt

def test_load_profile_has_both_registers():
    p = load_profile()
    assert "register_a" in p and "register_b" in p
    assert isinstance(p["register_a"]["signature_openers"], list)

def test_build_system_prompt_includes_register(monkeypatch, tmp_path):
    prompt_a = build_system_prompt(register="A", channel="linkedin")
    assert "LinkedIn" in prompt_a or "long-form" in prompt_a.lower()
    prompt_b = build_system_prompt(register="B", channel="social")
    assert "lowercase" in prompt_b.lower() or "short" in prompt_b.lower()
```

- [ ] **Step 3.2: Run to confirm FAIL**

```bash
pytest tests/content_hub/test_voice.py -v
```

- [ ] **Step 3.3: Implement `content_hub/generate/voice.py`**

```python
"""Alice voice profile: loader + extractor + system prompt builder."""
import argparse
import logging
from pathlib import Path
import yaml

from ..config import ANTHROPIC_API_KEY, VOICE_PROFILE_PATH, VOICE_SAMPLES_PATH

log = logging.getLogger(__name__)

EXTRACTION_PROMPT = """You are extracting a writer's voice profile from sample posts.
Read the samples, then emit a YAML document with this exact shape:

register_a:      # long-form professional
  signature_openers: [string, ...]    # 3-5 typical opening patterns
  rhythm: string                       # paragraph/stanza description
  list_style: string                   # e.g. 'arrow bullets, numbered frameworks'
  contrast_patterns: [string, ...]     # 2-4 contrast phrasings
  voice_markers: [string, ...]         # 3-6 phrases they reuse
  ctas_actually_used: [string, ...]    # real CTAs, verbatim
  hashtag_strategy: string
  dos: [string, ...]                   # 5-8 rules
  donts: [string, ...]                 # 5-8 rules
  sample_hooks: [string, ...]          # 3-5 verbatim hooks for few-shot

register_b:      # short casual (TikTok/Reel)
  <same keys as register_a>

Return ONLY the YAML. No preamble, no code fences."""


def load_samples() -> str:
    return VOICE_SAMPLES_PATH.read_text()


def rebuild() -> dict:
    import httpx
    samples = load_samples()
    r = httpx.post(
        "https://api.anthropic.com/v1/messages",
        headers={"x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"},
        json={
            "model": "claude-opus-4-7",
            "max_tokens": 4000,
            "system": EXTRACTION_PROMPT,
            "messages": [{"role": "user", "content": samples}],
        },
        timeout=120,
    )
    r.raise_for_status()
    yaml_text = r.json()["content"][0]["text"].strip()
    profile = yaml.safe_load(yaml_text)
    VOICE_PROFILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    VOICE_PROFILE_PATH.write_text(yaml_text)
    log.info("Wrote %s", VOICE_PROFILE_PATH)
    return profile


def load_profile() -> dict:
    if not VOICE_PROFILE_PATH.exists():
        return rebuild()
    return yaml.safe_load(VOICE_PROFILE_PATH.read_text())


def build_system_prompt(register: str, channel: str) -> str:
    p = load_profile()
    reg = p["register_a"] if register == "A" else p["register_b"]
    register_desc = "long-form professional" if register == "A" else "short casual TikTok/Reel"
    channel_label = {"linkedin": "LinkedIn", "youtube": "YouTube", "social": "Instagram/TikTok"}.get(channel, channel)
    return f"""You write in Alice Bazdikian's voice for {channel_label}.
Use the {register_desc} register.

SIGNATURE OPENERS:
{chr(10).join('- ' + o for o in reg['signature_openers'])}

RHYTHM: {reg['rhythm']}
LIST STYLE: {reg['list_style']}

CONTRAST PATTERNS:
{chr(10).join('- ' + c for c in reg['contrast_patterns'])}

VOICE MARKERS:
{chr(10).join('- ' + m for m in reg['voice_markers'])}

CTAs ALICE ACTUALLY USES:
{chr(10).join('- ' + c for c in reg['ctas_actually_used'])}

HASHTAG STRATEGY: {reg['hashtag_strategy']}

DO:
{chr(10).join('- ' + d for d in reg['dos'])}

DON'T:
{chr(10).join('- ' + d for d in reg['donts'])}

SAMPLE HOOKS (match this quality):
{chr(10).join('- ' + h for h in reg['sample_hooks'])}
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rebuild", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    if args.rebuild:
        rebuild()
        print("Voice profile rebuilt.")
    else:
        p = load_profile()
        print(f"Loaded profile with registers: {list(p.keys())}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 3.4: PASS**

```bash
pytest tests/content_hub/test_voice.py -v
```

- [ ] **Step 3.5: Generate the voice profile live (one-time)**

```bash
python -m content_hub.generate.voice --rebuild
cat content_hub/voice_samples/voice_profile.yaml | head -40
```
Expected: YAML with `register_a:` and `register_b:` keys populated. If the YAML is malformed, re-run; the Opus model occasionally adds code fences — strip them and re-save if so.

- [ ] **Step 3.6: Commit**

```bash
git add content_hub/generate/voice.py content_hub/voice_samples/voice_profile.yaml tests/content_hub/test_voice.py
git commit -m "feat(generate): voice profile extraction + system prompt builder"
```

---

## Task 4: CTA round-robin + hashtag composer (`generate/captions.py`)

**Files:**
- Create: `content_hub/generate/captions.py`
- Create: `tests/content_hub/test_captions.py`

- [ ] **Step 4.1: Write the failing tests**

```python
from content_hub.generate.captions import pick_ctas, compose_hashtags

def test_pick_ctas_round_robin_no_adjacent_duplicates():
    ctas = pick_ctas(n=6, channel="linkedin")
    assert len(ctas) == 6
    for i in range(len(ctas) - 1):
        assert ctas[i] != ctas[i + 1]

def test_compose_hashtags_includes_branded_and_niche():
    tags = compose_hashtags(channel="social")
    assert any(t.startswith("#AliceBazdikian") or t.startswith("#SmallBusinessAI") for t in tags)
    assert 5 <= len(tags) <= 12
```

- [ ] **Step 4.2: Run to confirm FAIL**

```bash
pytest tests/content_hub/test_captions.py -v
```

- [ ] **Step 4.3: Implement `content_hub/generate/captions.py`**

```python
"""CTA round-robin + hashtag composer."""
import itertools
from typing import Iterator

CTAS = {
    "linkedin": [
        "Book a free diagnostic — link in profile.",
        "DM me if you want help setting this up.",
        "Comment your biggest AI question below.",
        "Subscribe to my newsletter at smallbusinessaicoach.com.",
    ],
    "social": [
        "Link in bio.",
        "Save this for later.",
        "Follow for more AI for small business.",
        "DM me \"DIAGNOSTIC\" for a free session.",
    ],
    "youtube": [
        "Subscribe for weekly AI walkthroughs.",
        "Free templates at smallbusinessaicoach.com.",
    ],
}

HASHTAGS = {
    "linkedin": ["#AIforBusiness", "#ClaudeAI", "#SmallBusinessOwner",
                 "#AICoach", "#Entrepreneur", "#AIStrategy"],
    "social": ["#AIforBusiness", "#ClaudeAI", "#SmallBusinessAI",
               "#AIProductivity", "#Solopreneur", "#AICoach",
               "#AliceBazdikian", "#TechTok"],
    "youtube": ["#AIforBusiness", "#ClaudeAI", "#SmallBusinessAI"],
}


def _cycle(channel: str) -> Iterator[str]:
    return itertools.cycle(CTAS[channel])


def pick_ctas(n: int, channel: str) -> list[str]:
    it = _cycle(channel)
    return [next(it) for _ in range(n)]


def compose_hashtags(channel: str) -> list[str]:
    return list(HASHTAGS[channel])
```

- [ ] **Step 4.4: PASS + commit**

```bash
pytest tests/content_hub/test_captions.py -v && git add -A && git commit -m "feat(generate): CTA round-robin + hashtag composer"
```

---

## Task 5: Topic-fingerprint dedupe (`generate/fingerprint.py`)

**Files:**
- Create: `content_hub/generate/fingerprint.py`
- Create: `tests/content_hub/test_fingerprint.py`

- [ ] **Step 5.1: Write the failing tests**

```python
from content_hub.generate.fingerprint import fingerprint, dedupe

def test_fingerprint_normalizes_hooks():
    f1 = fingerprint("Stop paying for 7 AI tools")
    f2 = fingerprint("STOP PAYING FOR 7 AI TOOLS.")
    assert f1 == f2

def test_dedupe_keeps_highest_engagement():
    posts = [
        {"id": "a", "hook_line": "Stop paying for 7 AI tools", "likes": 100, "comments": 10},
        {"id": "b", "hook_line": "stop paying for 7 ai tools.", "likes": 500, "comments": 20},
        {"id": "c", "hook_line": "Totally different hook", "likes": 50, "comments": 5},
    ]
    out = dedupe(posts)
    ids = {p["id"] for p in out}
    assert "b" in ids and "c" in ids and "a" not in ids
```

- [ ] **Step 5.2: Run to confirm FAIL**

```bash
pytest tests/content_hub/test_fingerprint.py -v
```

- [ ] **Step 5.3: Implement `content_hub/generate/fingerprint.py`**

```python
"""Naive topic fingerprint: lowercase, strip punct, keep first 8 words."""
import re

_PUNCT = re.compile(r"[^\w\s]")


def fingerprint(text: str) -> str:
    t = _PUNCT.sub("", (text or "").lower()).strip()
    words = t.split()[:8]
    return " ".join(words)


def _engagement(p: dict) -> int:
    return int(p.get("likes", 0)) + int(p.get("comments", 0))


def dedupe(posts: list[dict]) -> list[dict]:
    by_fp: dict[str, dict] = {}
    for p in posts:
        fp = fingerprint(p.get("hook_line") or p.get("caption", "")[:120])
        if fp not in by_fp or _engagement(p) > _engagement(by_fp[fp]):
            by_fp[fp] = p
    return list(by_fp.values())
```

- [ ] **Step 5.4: PASS + commit**

```bash
pytest tests/content_hub/test_fingerprint.py -v && git add -A && git commit -m "feat(generate): topic-fingerprint dedupe for social"
```

---

## Task 6: Per-channel drafter (`generate/draft.py`)

**Files:**
- Create: `content_hub/generate/draft.py`
- Create: `tests/content_hub/test_draft.py`
- Create: `tests/content_hub/fixtures/source_post.json`

- [ ] **Step 6.1: Fixture source post**

`tests/content_hub/fixtures/source_post.json`:

```json
{
  "id": "tt_test_1",
  "channel": "tiktok",
  "creator_handle": "sabrina_ramonov",
  "caption": "Stop paying for 7 AI tools. Claude does all of them.",
  "hook_line": "Stop paying for 7 AI tools.",
  "format_tag": "short",
  "likes": 19800,
  "comments": 616,
  "views": 317700
}
```

- [ ] **Step 6.2: Write the failing test (uses monkeypatched Anthropic call)**

```python
import json
from pathlib import Path
from content_hub.generate.draft import generate_draft, register_for

FIXTURE = Path(__file__).parent / "fixtures" / "source_post.json"


def test_register_for_maps_channel():
    assert register_for("linkedin") == "A"
    assert register_for("youtube") == "A"
    assert register_for("social") == "B"


def test_generate_draft_returns_complete_draft(monkeypatch):
    import content_hub.generate.draft as draft_mod
    fake_json = {
        "hook": "Your 7 AI tools are a subscription trap.",
        "slides": [
            {"kind": "cover", "title": "Your 7 AI tools are a trap.", "body": ""},
            {"kind": "content", "title": "The problem", "body": "Paying for 7 tools."},
            {"kind": "content", "title": "The fix", "body": "Claude does it all."},
            {"kind": "cta", "title": "Link in bio", "body": "Book free diagnostic."},
        ],
        "caption": "your 7 ai tools are a trap 😮‍💨 ...",
        "cta": "Link in bio.",
        "hashtags": ["#AIforBusiness", "#ClaudeAI"],
    }
    monkeypatch.setattr(draft_mod, "_call_claude", lambda *a, **kw: fake_json)

    post = json.loads(FIXTURE.read_text())
    d = generate_draft(post, channel="social")
    assert d.channel == "social"
    assert d.register == "B"
    assert d.source_post_id == "tt_test_1"
    assert len(d.slides) == 4
    assert d.slides[0].kind == "cover"
    assert len(d.hashtags) >= 2
```

- [ ] **Step 6.3: Run to confirm FAIL**

```bash
pytest tests/content_hub/test_draft.py -v
```

- [ ] **Step 6.4: Implement `content_hub/generate/draft.py`**

```python
"""Per-channel drafter using Claude Sonnet."""
import json
import logging
from typing import Any

import httpx

from ..config import ANTHROPIC_API_KEY, CAPTION_LIMITS, DRAFTER_MODEL, SLIDES_PER_CAROUSEL
from .models import Draft, SlideContent
from .voice import build_system_prompt

log = logging.getLogger(__name__)

REGISTER_MAP = {"linkedin": "A", "youtube": "A", "social": "B"}


def register_for(channel: str) -> str:
    return REGISTER_MAP.get(channel, "A")


SHAPE_INSTRUCTIONS = {
    "social": (
        "Output a carousel of exactly {n_slides} slides for IG/TT: "
        "1 cover (hook only), {n_body} body slides (each with a short title + 1-2 line body), "
        "1 CTA slide. Caption <= {caplimit} words, lowercase register, ends with Alice's typical CTA."
    ),
    "linkedin": (
        "Output {n_slides} slides for a LinkedIn PDF carousel: 1 cover, {n_body} body, 1 CTA. "
        "Caption <= {caplimit} words, professional register, ends with CTA + 6-10 hashtags."
    ),
    "youtube": (
        "Output a recording-guide deck of 8 slides: 1 title, 6 talking-point slides "
        "(big readable text, 1 idea per slide), 1 closing CTA slide. "
        "Also return a caption for the YouTube description <= {caplimit} words."
    ),
}

USER_TEMPLATE = """Source post to rewrite in Alice's voice:

Creator: @{creator_handle}
Channel: {src_channel}
Hook: {hook}
Caption:
{caption}

Engagement: {likes} likes, {comments} comments, {views} views

{shape}

Reply ONLY with a JSON object:
{{
  "hook": "...",
  "slides": [{{"kind": "cover|content|cta", "title": "...", "body": "..."}}, ...],
  "caption": "...",
  "cta": "...",
  "hashtags": ["#...", ...]
}}
No code fences. No preamble."""


def _call_claude(system: str, user: str) -> dict[str, Any]:
    r = httpx.post(
        "https://api.anthropic.com/v1/messages",
        headers={"x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"},
        json={
            "model": DRAFTER_MODEL,
            "max_tokens": 3000,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        },
        timeout=120,
    )
    r.raise_for_status()
    text = r.json()["content"][0]["text"].strip()
    if text.startswith("```"):
        text = text.strip("`").split("\n", 1)[1].rsplit("```", 1)[0]
    return json.loads(text)


def generate_draft(post: dict, channel: str) -> Draft:
    reg = register_for(channel)
    n_slides = SLIDES_PER_CAROUSEL.get(channel, 8)
    n_body = n_slides - 2
    shape = SHAPE_INSTRUCTIONS[channel].format(
        n_slides=n_slides, n_body=n_body, caplimit=CAPTION_LIMITS[channel]
    )
    system = build_system_prompt(register=reg, channel=channel)
    user = USER_TEMPLATE.format(
        creator_handle=post.get("creator_handle", "unknown"),
        src_channel=post.get("channel", ""),
        hook=post.get("hook_line") or post.get("caption", "")[:120],
        caption=post.get("caption", ""),
        likes=post.get("likes", 0),
        comments=post.get("comments", 0),
        views=post.get("views", 0),
        shape=shape,
    )
    try:
        data = _call_claude(system, user)
    except Exception:
        log.exception("Drafter call failed for post %s", post.get("id"))
        raise
    return Draft(
        source_post_id=post["id"],
        channel=channel,
        register=reg,
        hook=data["hook"],
        slides=[SlideContent(**s) for s in data["slides"]],
        caption=data["caption"],
        cta=data.get("cta", ""),
        hashtags=data.get("hashtags", []),
    )
```

- [ ] **Step 6.5: PASS + commit**

```bash
pytest tests/content_hub/test_draft.py -v && git add -A && git commit -m "feat(generate): per-channel Claude drafter with register selection"
```

---

## Task 7: Carousel JPG renderer (`render/carousel_jpg.py`)

**Files:**
- Create: `content_hub/render/carousel_jpg.py`
- Create: `tests/content_hub/test_carousel_jpg.py`
- Reuse: `social-pipeline/templates/carousel_cover.html`, `carousel_content.html`, `carousel_cta.html`

- [ ] **Step 7.1: Write the failing test**

```python
from pathlib import Path
from content_hub.render.carousel_jpg import render_slides
from content_hub.generate.models import Draft, SlideContent

def test_render_slides_produces_jpg_per_slide(tmp_path):
    d = Draft(
        source_post_id="t1", channel="social", register="B",
        hook="Hook", caption="c", cta="Link in bio.",
        slides=[
            SlideContent(kind="cover", title="Hook", body=""),
            SlideContent(kind="content", title="Point 1", body="Body"),
            SlideContent(kind="cta", title="Link in bio", body="Book a diagnostic."),
        ],
        hashtags=["#x"],
    )
    paths = render_slides(d, tmp_path, width=1080, height=1350)
    assert len(paths) == 3
    for p in paths:
        assert Path(p).exists() and Path(p).stat().st_size > 5_000
```

- [ ] **Step 7.2: Run to confirm FAIL**

```bash
pytest tests/content_hub/test_carousel_jpg.py -v
```

- [ ] **Step 7.3: Implement `content_hub/render/carousel_jpg.py`**

```python
"""Render a Draft's slides to JPGs via Playwright, reusing social-pipeline templates."""
from pathlib import Path
import asyncio
from jinja2 import Environment, FileSystemLoader
from playwright.async_api import async_playwright

from ..generate.models import Draft

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
TEMPLATES_DIR = PROJECT_ROOT / "social-pipeline" / "templates"

_TEMPLATE_FOR = {
    "cover": "carousel_cover.html",
    "content": "carousel_content.html",
    "cta": "carousel_cta.html",
}

env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=True)


async def _render_one(html: str, out: Path, width: int, height: int) -> None:
    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        page = await browser.new_page(viewport={"width": width, "height": height})
        await page.set_content(html, wait_until="networkidle")
        await page.screenshot(path=str(out), type="jpeg", quality=92, full_page=False)
        await browser.close()


def render_slides(draft: Draft, out_dir: Path, width: int = 1080, height: int = 1350) -> list[Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    total = len(draft.slides)
    for i, slide in enumerate(draft.slides, start=1):
        tpl = env.get_template(_TEMPLATE_FOR.get(slide.kind, "carousel_content.html"))
        html = tpl.render(
            title=slide.title, body=slide.body,
            slide_n=i, total=total,
            hook=draft.hook, cta=draft.cta,
            website="smallbusinessaicoach.com",
            name="Alice Bazdikian",
        )
        out = out_dir / f"{i:02d}.jpg"
        asyncio.run(_render_one(html, out, width, height))
        paths.append(out)
    return paths
```

- [ ] **Step 7.4: PASS + commit**

```bash
pytest tests/content_hub/test_carousel_jpg.py -v && git add -A && git commit -m "feat(render): carousel JPG renderer via Playwright"
```

**Note:** if `social-pipeline/templates/carousel_*.html` don't accept these variables, update the templates to include `{{ name }}` + `{{ website }}` at the footer and `{{ slide_n }}/{{ total }}` as a page indicator. Make this a separate commit.

---

## Task 8: Carousel MP4 renderer (`render/carousel_video.py`)

**Files:**
- Create: `content_hub/render/carousel_video.py`
- Create: `tests/content_hub/test_carousel_video.py`

- [ ] **Step 8.1: Verify ffmpeg present**

```bash
which ffmpeg || brew install ffmpeg
```

- [ ] **Step 8.2: Write the failing test**

```python
from pathlib import Path
from PIL import Image
from content_hub.render.carousel_video import slides_to_mp4

def test_slides_to_mp4_creates_nonzero_file(tmp_path):
    for i in range(3):
        img = Image.new("RGB", (1080, 1350), (122, 31, 43))
        img.save(tmp_path / f"{i+1:02d}.jpg")
    out = tmp_path / "carousel.mp4"
    slides_to_mp4(sorted(tmp_path.glob("*.jpg")), out, seconds_per_slide=1)
    assert out.exists() and out.stat().st_size > 10_000
```

(requires Pillow — add to requirements if not already; `pillow>=10`)

- [ ] **Step 8.3: Run to confirm FAIL**

- [ ] **Step 8.4: Implement `content_hub/render/carousel_video.py`**

```python
"""JPG carousel → MP4 via ffmpeg."""
import subprocess
import tempfile
from pathlib import Path


def slides_to_mp4(jpgs: list[Path], out: Path, seconds_per_slide: int = 5) -> Path:
    jpgs = [Path(p) for p in jpgs]
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        for j in jpgs:
            f.write(f"file '{j.resolve()}'\n")
            f.write(f"duration {seconds_per_slide}\n")
        f.write(f"file '{jpgs[-1].resolve()}'\n")
        listfile = f.name
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", listfile,
         "-vf", "fps=30,format=yuv420p", "-c:v", "libx264", "-preset", "medium",
         str(out)],
        check=True, capture_output=True,
    )
    return out
```

- [ ] **Step 8.5: PASS + commit**

---

## Task 9: LinkedIn PDF renderer (`render/linkedin_pdf.py`)

**Files:**
- Create: `content_hub/render/linkedin_pdf.py`
- Create: `tests/content_hub/test_linkedin_pdf.py`

- [ ] **Step 9.1: Write the failing test**

```python
from content_hub.render.linkedin_pdf import make_pdf
from content_hub.generate.models import Draft, SlideContent

def test_make_pdf_produces_pdf_bytes(tmp_path):
    d = Draft(source_post_id="x", channel="linkedin", register="A",
              hook="H", caption="c", cta="Book a free diagnostic.",
              slides=[SlideContent(kind="cover", title="H", body=""),
                      SlideContent(kind="content", title="T", body="B"),
                      SlideContent(kind="cta", title="Book", body="diagnostic")],
              hashtags=["#x"])
    out = tmp_path / "carousel.pdf"
    make_pdf(d, out)
    header = out.read_bytes()[:4]
    assert header == b"%PDF"
```

- [ ] **Step 9.2: Run to confirm FAIL**

- [ ] **Step 9.3: Implement `content_hub/render/linkedin_pdf.py`**

```python
"""Render LinkedIn PDF carousel: one page per slide via Playwright PDF."""
import asyncio
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from playwright.async_api import async_playwright

from ..generate.models import Draft
from .carousel_jpg import TEMPLATES_DIR, _TEMPLATE_FOR

env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=True)

PAGE_WRAPPER = """<!doctype html><html><head><meta charset=utf-8>
<style>@page {{ size: 1200px 1500px; margin: 0; }} body {{ margin: 0; }}
.page {{ width: 1200px; height: 1500px; page-break-after: always; }}</style></head>
<body>{pages}</body></html>"""


async def _render(html: str, out: Path) -> None:
    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        page = await browser.new_page()
        await page.set_content(html, wait_until="networkidle")
        await page.pdf(path=str(out), width="1200px", height="1500px",
                       print_background=True, margin={"top":"0","bottom":"0","left":"0","right":"0"})
        await browser.close()


def make_pdf(draft: Draft, out: Path) -> Path:
    pages = []
    total = len(draft.slides)
    for i, slide in enumerate(draft.slides, start=1):
        tpl = env.get_template(_TEMPLATE_FOR.get(slide.kind, "carousel_content.html"))
        body = tpl.render(title=slide.title, body=slide.body,
                          slide_n=i, total=total, hook=draft.hook, cta=draft.cta,
                          website="smallbusinessaicoach.com", name="Alice Bazdikian")
        pages.append(f'<div class="page">{body}</div>')
    html = PAGE_WRAPPER.format(pages="".join(pages))
    asyncio.run(_render(html, out))
    return out
```

- [ ] **Step 9.4: PASS + commit**

---

## Task 10: YouTube Google Slides deck (`render/yt_slides.py`)

**Files:**
- Create: `content_hub/render/yt_slides.py`
- Create: `tests/content_hub/test_yt_slides.py`

- [ ] **Step 10.1: Add Google service account JSON path to config**

Append to `content_hub/config.py`:

```python
GOOGLE_SA_JSON = os.environ.get("GOOGLE_SA_JSON", str(PROJECT_ROOT / "content_hub" / ".credentials" / "service-account.json"))
```

Alice needs to create a Google Cloud service account, enable Slides + Drive APIs, download the JSON, and drop it at that path. Document in README.

- [ ] **Step 10.2: Write the failing test (monkeypatched API)**

```python
from content_hub.render.yt_slides import build_slide_requests
from content_hub.generate.models import Draft, SlideContent

def test_build_slide_requests_creates_one_per_slide():
    d = Draft(source_post_id="y", channel="youtube", register="A",
              hook="H", caption="c", cta="",
              slides=[SlideContent(kind="cover", title="Hook", body=""),
                      SlideContent(kind="content", title="Point", body="Body line.")],
              hashtags=[])
    reqs = build_slide_requests(d, presentation_id="fake_id")
    slide_inserts = [r for r in reqs if "createSlide" in r]
    assert len(slide_inserts) == 2
```

- [ ] **Step 10.3: Run to confirm FAIL**

- [ ] **Step 10.4: Implement `content_hub/render/yt_slides.py`**

```python
"""Create Google Slides decks for YouTube recording guides."""
from pathlib import Path
from google.oauth2 import service_account
from googleapiclient.discovery import build

from ..config import GOOGLE_SA_JSON
from ..generate.models import Draft

SCOPES = ["https://www.googleapis.com/auth/presentations", "https://www.googleapis.com/auth/drive"]


def _services():
    creds = service_account.Credentials.from_service_account_file(GOOGLE_SA_JSON, scopes=SCOPES)
    return build("slides", "v1", credentials=creds), build("drive", "v3", credentials=creds)


def build_slide_requests(draft: Draft, presentation_id: str) -> list[dict]:
    reqs: list[dict] = []
    for i, slide in enumerate(draft.slides):
        obj_id = f"slide_{i}"
        reqs.append({"createSlide": {
            "objectId": obj_id,
            "insertionIndex": i + 1,
            "slideLayoutReference": {"predefinedLayout": "BLANK"},
        }})
        reqs.append({"insertText": {
            "objectId": obj_id + "_title",
            "text": slide.title,
        }})
        reqs.append({"insertText": {
            "objectId": obj_id + "_body",
            "text": slide.body,
        }})
    return reqs


def create_deck(draft: Draft, drive_parent_folder: str) -> str:
    """Create a deck in Drive; return the presentation URL."""
    slides, drive = _services()
    pres = slides.presentations().create(body={"title": draft.hook[:60]}).execute()
    pid = pres["presentationId"]
    drive.files().update(fileId=pid, addParents=drive_parent_folder, fields="id, parents").execute()
    slides.presentations().batchUpdate(
        presentationId=pid, body={"requests": build_slide_requests(draft, pid)}
    ).execute()
    return f"https://docs.google.com/presentation/d/{pid}/edit"
```

- [ ] **Step 10.5: PASS the unit test + commit**

(Full integration with live API is validated in Task 15 end-to-end.)

---

## Task 11: Drive client + weekly layout + SUMMARY (`drive/`)

**Files:**
- Create: `content_hub/drive/client.py`
- Create: `content_hub/drive/layout.py`
- Create: `tests/content_hub/test_drive_layout.py`

- [ ] **Step 11.1: Write failing test for `build_summary_md` (pure function, no Drive calls)**

```python
from content_hub.drive.layout import build_summary_md
from content_hub.generate.models import Draft, SlideContent

def test_build_summary_md_lists_every_draft():
    drafts = [
        Draft(source_post_id="a", channel="linkedin", register="A", hook="Hook A",
              caption="c", cta="", slides=[SlideContent(kind="cover", title="H", body="")], hashtags=[]),
        Draft(source_post_id="b", channel="social", register="B", hook="Hook B",
              caption="c", cta="", slides=[SlideContent(kind="cover", title="H", body="")], hashtags=[]),
    ]
    links = {"a": "https://drive.google.com/a", "b": "https://drive.google.com/b"}
    md = build_summary_md(week_id="2026-04-13", drafts=drafts, drive_links=links)
    assert "Hook A" in md and "Hook B" in md
    assert "drive.google.com/a" in md
    assert "# Content Hub · Week of 2026-04-13" in md
```

- [ ] **Step 11.2: Run to confirm FAIL**

- [ ] **Step 11.3: Implement `content_hub/drive/client.py`**

```python
"""Google Drive API service via service account."""
from google.oauth2 import service_account
from googleapiclient.discovery import build

from ..config import GOOGLE_SA_JSON

SCOPES = ["https://www.googleapis.com/auth/drive"]


def get_service():
    creds = service_account.Credentials.from_service_account_file(GOOGLE_SA_JSON, scopes=SCOPES)
    return build("drive", "v3", credentials=creds)


def ensure_folder(parent_id: str, name: str) -> str:
    svc = get_service()
    q = f"'{parent_id}' in parents and name = '{name}' and mimeType = 'application/vnd.google-apps.folder' and trashed=false"
    res = svc.files().list(q=q, fields="files(id,name)").execute()
    if res.get("files"):
        return res["files"][0]["id"]
    body = {"name": name, "mimeType": "application/vnd.google-apps.folder", "parents": [parent_id]}
    return svc.files().create(body=body, fields="id").execute()["id"]


def upload_file(local_path: str, parent_id: str, name: str | None = None, mime: str = "application/octet-stream") -> str:
    from googleapiclient.http import MediaFileUpload
    svc = get_service()
    media = MediaFileUpload(local_path, mimetype=mime)
    body = {"name": name or local_path.rsplit("/", 1)[-1], "parents": [parent_id]}
    f = svc.files().create(body=body, media_body=media, fields="id, webViewLink").execute()
    return f["webViewLink"]
```

- [ ] **Step 11.4: Implement `content_hub/drive/layout.py`**

```python
"""Week folder layout + SUMMARY.md writer."""
from pathlib import Path
from typing import Iterable

from ..generate.models import Draft
from ..config import DRIVE_ROOT_FOLDER_ID
from .client import ensure_folder, upload_file


def build_summary_md(week_id: str, drafts: Iterable[Draft], drive_links: dict[str, str]) -> str:
    buckets: dict[str, list[Draft]] = {}
    for d in drafts:
        buckets.setdefault(d.channel, []).append(d)
    out = [f"# Content Hub · Week of {week_id}\n"]
    out.append("Reply **Done** to the approval email once you've edited everything you want to publish.\n")
    for ch in ("youtube", "linkedin", "social"):
        if ch not in buckets:
            continue
        out.append(f"\n## {ch.capitalize()}\n")
        for d in buckets[ch]:
            link = drive_links.get(d.source_post_id, "")
            out.append(f"- **{d.hook}**  \n  [Edit in Drive →]({link})")
    return "\n".join(out)


def create_week_folders(week_id: str) -> dict[str, str]:
    root = DRIVE_ROOT_FOLDER_ID
    week = ensure_folder(root, week_id)
    return {
        "week": week,
        "youtube": ensure_folder(week, "youtube"),
        "linkedin": ensure_folder(week, "linkedin"),
        "social": ensure_folder(week, "social"),
    }


def upload_summary(week_folder_id: str, markdown: str) -> str:
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
        f.write(markdown)
        path = f.name
    return upload_file(path, week_folder_id, "SUMMARY.md", mime="text/markdown")
```

- [ ] **Step 11.5: PASS + commit**

---

## Task 12: Email digest (`email_digest/`)

**Files:**
- Create: `content_hub/email_digest/render.py`
- Create: `content_hub/email_digest/templates/digest.html`
- Create: `content_hub/email_digest/send.py`
- Create: `content_hub/email_digest/reply_parser.py`
- Create: `tests/content_hub/test_email_digest.py`
- Create: `tests/content_hub/test_reply_parser.py`

- [ ] **Step 12.1: Write the failing test for digest HTML**

```python
from content_hub.email_digest.render import render_digest
from content_hub.generate.models import Draft, SlideContent

def test_render_digest_includes_every_hook():
    drafts = [
        Draft(source_post_id="a", channel="linkedin", register="A",
              hook="Claude is a strategist", caption="c" * 50, cta="",
              slides=[SlideContent(kind="cover", title="H", body="")], hashtags=["#x"]),
        Draft(source_post_id="b", channel="social", register="B",
              hook="lazy install", caption="c", cta="link in bio",
              slides=[SlideContent(kind="cover", title="H", body="")], hashtags=[]),
    ]
    html = render_digest(week_id="2026-04-13", drafts=drafts,
                         drive_links={"a": "https://drive/a", "b": "https://drive/b"})
    assert "Claude is a strategist" in html
    assert "lazy install" in html
    assert "Reply **Done**" in html or "Reply Done" in html
    assert "https://drive/a" in html
```

- [ ] **Step 12.2: Write the failing test for reply parser**

```python
from content_hub.email_digest.reply_parser import is_done

def test_is_done_first_word_case_insensitive():
    assert is_done("Done")
    assert is_done("done thanks")
    assert is_done("DONE!")
    assert not is_done("Looks great")
    assert not is_done("")
```

- [ ] **Step 12.3: Run both tests to confirm FAIL**

- [ ] **Step 12.4: Implement `content_hub/email_digest/reply_parser.py`**

```python
import re
_DONE = re.compile(r"^\s*done\b", re.IGNORECASE)

def is_done(body: str) -> bool:
    return bool(_DONE.match(body or ""))
```

- [ ] **Step 12.5: Implement `content_hub/email_digest/templates/digest.html`**

```html
<!doctype html>
<html><head><meta charset="utf-8"><style>
  body { font-family: -apple-system, sans-serif; background: #F7F3EE; color: #1F1A17; padding: 24px; }
  .header { color: #7A1F2B; font-family: Georgia, serif; font-size: 28px; letter-spacing: -0.02em; }
  .section-title { color: #C9A24B; text-transform: uppercase; letter-spacing: 0.15em; font-size: 12px; margin-top: 32px; }
  .card { background: white; border: 1px solid #E2D9CC; border-radius: 10px; padding: 20px; margin: 12px 0; }
  .hook { font-family: Georgia, serif; font-size: 20px; color: #1F1A17; margin: 0 0 8px; }
  .meta { font-size: 12px; color: #7A6E63; margin-bottom: 12px; }
  .caption { font-size: 14px; color: #1F1A17; line-height: 1.5; margin-bottom: 16px; }
  .btn { display: inline-block; padding: 10px 18px; background: #7A1F2B; color: white; border-radius: 8px; text-decoration: none; font-weight: 600; }
  .footer { margin-top: 40px; padding-top: 20px; border-top: 1px solid #E2D9CC; font-size: 14px; }
</style></head><body>
<div class="header">Content Hub · Week of {{ week_id }}</div>
{% for channel, drafts in buckets.items() %}
<div class="section-title">{{ channel }}</div>
{% for d in drafts %}
<div class="card">
  <p class="hook">{{ d.hook }}</p>
  <div class="meta">Source: @{{ d.source_post_id }} · {{ d.channel }} · {{ d.register }}</div>
  <div class="caption">{{ d.caption[:300] }}{% if d.caption|length > 300 %}…{% endif %}</div>
  <a class="btn" href="{{ drive_links[d.source_post_id] }}">Edit in Drive →</a>
</div>
{% endfor %}
{% endfor %}
<div class="footer">Reply <strong>Done</strong> to this email when you've edited everything you want to publish.</div>
</body></html>
```

- [ ] **Step 12.6: Implement `content_hub/email_digest/render.py`**

```python
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from ..generate.models import Draft

env = Environment(loader=FileSystemLoader(str(Path(__file__).parent / "templates")), autoescape=True)


def render_digest(week_id: str, drafts: list[Draft], drive_links: dict[str, str]) -> str:
    buckets: dict[str, list[Draft]] = {}
    for d in drafts:
        buckets.setdefault(d.channel, []).append(d)
    return env.get_template("digest.html").render(
        week_id=week_id, buckets=buckets, drive_links=drive_links,
    )
```

- [ ] **Step 12.7: Implement `content_hub/email_digest/send.py`**

```python
"""Gmail sender — reuses social-pipeline OAuth creds."""
import base64
import sys
from email.mime.text import MIMEText
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "social-pipeline"))
from gmail_auth import get_service  # type: ignore


def send_html(to: str, subject: str, html: str) -> str:
    msg = MIMEText(html, "html")
    msg["to"] = to
    msg["subject"] = subject
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    svc = get_service()
    sent = svc.users().messages().send(userId="me", body={"raw": raw}).execute()
    return sent["id"]
```

- [ ] **Step 12.8: PASS all digest tests + commit**

```bash
pytest tests/content_hub/test_email_digest.py tests/content_hub/test_reply_parser.py -v
git add -A && git commit -m "feat(email): weekly digest + strict Done parser"
```

---

## Task 13: Dashboard change — merge IG + TT into `social`

**Files:**
- Modify: `content_hub/config.py`
- Modify: `content_hub/scheduler.py`
- Modify: `content_hub/app.py`

- [ ] **Step 13.1: Update `CHANNELS` tuple in `content_hub/config.py`**

Change:

```python
CHANNELS = ["youtube", "linkedin", "tiktok", "instagram"]
```
to:

```python
CHANNELS = ["youtube", "linkedin", "social"]
```

And keep `CREATORS` and `HASHTAGS` keyed by the underlying `instagram`/`tiktok` keys for the scheduler — add a `SOCIAL_SOURCES = ["instagram", "tiktok"]` list.

- [ ] **Step 13.2: Update `content_hub/scheduler.py`**

In `pull_week()`, keep fetching separately for `instagram` and `tiktok` (they use different Apify actors), but when writing posts to DB, tag them with `channel="social"` and put the original channel in `raw_json` under `_source_channel`.

After writing, call `fingerprint.dedupe()` on the social bucket before insertion.

- [ ] **Step 13.3: Update `content_hub/app.py`** — no change needed; channel list comes from `CHANNELS` already.

- [ ] **Step 13.4: Smoke test**

```bash
python -m content_hub.scheduler --fixtures
uvicorn content_hub.app:app --port 4000 --log-level warning &
curl -s -o /dev/null -w "%{http_code}\n" "http://localhost:4000/week/$(date +%F -v-Mon)?channel=social"
pkill -f "uvicorn content_hub"
```
Expected: `200`.

- [ ] **Step 13.5: Commit**

---

## Task 14: Orchestrator — wire everything (`jobs/orchestrator.py` + worker)

**Files:**
- Create: `content_hub/jobs/orchestrator.py`
- Modify: `content_hub/jobs/create_worker.py`
- Create: `tests/content_hub/test_orchestrator.py`

- [ ] **Step 14.1: Write failing test (all external calls mocked)**

```python
from unittest.mock import patch, MagicMock
from content_hub.jobs.orchestrator import run_job
from content_hub.generate.models import Draft, SlideContent

@patch("content_hub.jobs.orchestrator.generate_draft")
@patch("content_hub.jobs.orchestrator.render_slides")
@patch("content_hub.jobs.orchestrator.slides_to_mp4")
@patch("content_hub.jobs.orchestrator.make_pdf")
@patch("content_hub.jobs.orchestrator.create_deck", return_value="https://slides/x")
@patch("content_hub.jobs.orchestrator.create_week_folders",
       return_value={"week":"w","youtube":"y","linkedin":"l","social":"s"})
@patch("content_hub.jobs.orchestrator.upload_file", return_value="https://drive/u")
@patch("content_hub.jobs.orchestrator.upload_summary", return_value="https://drive/s")
@patch("content_hub.jobs.orchestrator.send_html", return_value="msg_1")
def test_run_job_end_to_end(send_h, u_sum, up, folders, deck, pdf, mp4, ren, gen, tmp_path):
    gen.return_value = Draft(source_post_id="p1", channel="social", register="B",
                             hook="H", caption="c", cta="",
                             slides=[SlideContent(kind="cover", title="H", body="")], hashtags=[])
    ren.return_value = [tmp_path / "01.jpg"]

    job = {"id": 1, "week_id": "2026-04-13", "channel": "social",
           "payload_json": '{"post_ids":["p1"],"pasted_urls":[]}'}
    selected = [{"id": "p1", "channel": "social", "caption": "c", "hook_line": "H"}]

    result = run_job(job, selected_posts=selected)
    assert result["digest_email_id"] == "msg_1"
    assert gen.called and send_h.called
```

- [ ] **Step 14.2: Implement `content_hub/jobs/orchestrator.py`**

```python
"""End-to-end content generation pipeline for a single Create-job."""
import json
import logging
import tempfile
from pathlib import Path

from ..config import ALICE_EMAIL
from ..drive.client import upload_file
from ..drive.layout import build_summary_md, create_week_folders, upload_summary
from ..email_digest.render import render_digest
from ..email_digest.send import send_html
from ..generate.draft import generate_draft
from ..generate.fingerprint import dedupe
from ..generate.models import Draft
from ..render.carousel_jpg import render_slides
from ..render.carousel_video import slides_to_mp4
from ..render.linkedin_pdf import make_pdf
from ..render.yt_slides import create_deck

log = logging.getLogger(__name__)


def _render_and_upload(draft: Draft, channel: str, folders: dict, workdir: Path) -> str:
    """Render final files per channel; return the primary Drive link."""
    slot = workdir / draft.source_post_id
    slot.mkdir(parents=True, exist_ok=True)
    if channel == "social":
        jpgs = render_slides(draft, slot, width=1080, height=1350)
        mp4 = slot / "carousel.mp4"
        slides_to_mp4(jpgs, mp4)
        primary = upload_file(str(mp4), folders["social"], name=f"{draft.source_post_id}.mp4", mime="video/mp4")
        for j in jpgs:
            upload_file(str(j), folders["social"], name=f"{draft.source_post_id}_{j.name}", mime="image/jpeg")
        return primary
    if channel == "linkedin":
        pdf = slot / "carousel.pdf"
        make_pdf(draft, pdf)
        return upload_file(str(pdf), folders["linkedin"], name=f"{draft.source_post_id}.pdf", mime="application/pdf")
    if channel == "youtube":
        return create_deck(draft, folders["youtube"])
    raise ValueError(f"Unknown channel {channel}")


def run_job(job: dict, selected_posts: list[dict]) -> dict:
    payload = json.loads(job["payload_json"])
    channel = job["channel"]
    week_id = job["week_id"]
    log.info("Orchestrator: job %s channel=%s posts=%d", job["id"], channel, len(selected_posts))

    posts = dedupe(selected_posts) if channel == "social" else selected_posts

    drafts = [generate_draft(p, channel=channel) for p in posts]

    folders = create_week_folders(week_id)
    with tempfile.TemporaryDirectory() as td:
        workdir = Path(td)
        drive_links = {d.source_post_id: _render_and_upload(d, channel, folders, workdir) for d in drafts}

    summary_md = build_summary_md(week_id, drafts, drive_links)
    summary_link = upload_summary(folders["week"], summary_md)

    digest_html = render_digest(week_id, drafts, drive_links)
    msg_id = send_html(
        to=ALICE_EMAIL,
        subject=f"[Content Hub] {channel} drafts ready · week of {week_id}",
        html=digest_html,
    )

    return {
        "channel": channel,
        "drafts": [d.source_post_id for d in drafts],
        "drive_links": drive_links,
        "summary_link": summary_link,
        "digest_email_id": msg_id,
    }
```

- [ ] **Step 14.3: Replace the stub in `content_hub/jobs/create_worker.py`**

In `handle()`, replace the whole function body with:

```python
def handle(job: dict) -> dict:
    from .. import db
    from .orchestrator import run_job
    payload = json.loads(job["payload_json"] or "{}")
    selected = db.selected_posts(job["week_id"], job["channel"])
    # Include pasted URLs — for now, treat as future on-demand fetch (Task 15).
    return run_job(job, selected_posts=selected)
```

- [ ] **Step 14.4: PASS orchestrator test + commit**

---

## Task 15: End-to-end live smoke test

- [ ] **Step 15.1: Reset the queued jobs from earlier session** (they reference old pre-`social` channels):

```bash
python -c "import sqlite3; c=sqlite3.connect('content_hub/hub.db'); c.execute(\"UPDATE jobs SET status='cancelled' WHERE status='queued'\"); c.commit()"
```

- [ ] **Step 15.2: Run scheduler + pick 1 post per channel on the dashboard**

```bash
python -m content_hub.scheduler
uvicorn content_hub.app:app --port 4000 --log-level warning &
```

Open http://localhost:4000, check 1 post on each of `youtube`, `linkedin`, `social`, click Create on each.

- [ ] **Step 15.3: Start the worker**

```bash
python -m content_hub.jobs.create_worker
```

- [ ] **Step 15.4: Verify**
  1. Gmail inbox receives 3 emails (one per channel) with subject `[Content Hub] ... drafts ready`.
  2. Drive has `/Content Hub/<week_id>/` with `youtube/`, `linkedin/`, `social/`, `SUMMARY.md`.
  3. `hub.db`: `jobs` table has all 3 rows with `status='done'`.

- [ ] **Step 15.5: Simulate approval**
Reply `Done` to one of the emails. The reply-watcher is NOT implemented yet in this plan — file a follow-up plan for `drive/watch.py` + `/READY-TO-POST/` re-render. Mark this task done once the forward path works end-to-end.

- [ ] **Step 15.6: Commit final state + tag**

```bash
git commit --allow-empty -m "chore: content generation worker end-to-end smoke passed"
git tag content-gen-v1
```

---

## Deferred to a follow-up plan (not in this plan's scope)

- `drive/watch.py` and the `/READY-TO-POST/` re-render path on `Done` reply. Needs Drive change-watcher + monitor_reply integration.
- Pasted-URL on-demand fetch in the worker (currently ignored — only pre-scraped posts in the DB are used).
- Voice profile auto-refresh when `alice_posts.md` changes (currently manual `--rebuild`).
- Batch-level CTA round-robin across drafts in one job.
