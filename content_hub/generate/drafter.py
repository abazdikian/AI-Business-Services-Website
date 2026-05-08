"""Claude-Sonnet drafter: competitor post → Alice-voice draft for one channel.

Two entry points:
  draft_post         → single body string (YouTube description path uses this)
  draft_carousel     → {slides: [...], caption: "..."} for carousel channels
"""

import json
import logging
import re
from typing import Any

import httpx

from ..config import ANTHROPIC_API_KEY

log = logging.getLogger(__name__)

SONNET_MODEL = "claude-sonnet-4-6"

REGISTER_A = {"linkedin", "instagram", "youtube"}
REGISTER_B = {"tiktok"}

ALICE_POSITIONING = """\
Alice Bazdikian is a small-business AI coach. She teaches solopreneurs and
small-team founders — especially women in small business — to use Claude
(Code, Cowork, Chat) as a strategist and operator, not a chatbot. Offers:
free AI diagnostic, paid Accelerator cohort, Claude Cowork coaching.
Brand colors: burgundy / gold / eggshell. Site: smallbusinessaicoach.com.
"""


def _register_for(channel: str) -> str:
    if channel in REGISTER_B:
        return "B (short casual)"
    return "A (long-form professional)"


def _system_prompt(channel: str, voice_profile: str) -> str:
    register = _register_for(channel)
    return (
        "You draft social posts in Alice Bazdikian's voice.\n\n"
        f"=== WHO ALICE IS ===\n{ALICE_POSITIONING}\n"
        f"=== TARGET CHANNEL ===\n{channel}\n"
        f"=== TARGET REGISTER ===\n{register}\n"
        "Follow the register rules in the VOICE PROFILE below. If the channel is "
        "TikTok or a short Reel, use Register B. Otherwise use Register A.\n\n"
        "=== VOICE PROFILE (rules + exemplars) ===\n"
        f"{voice_profile}\n\n"
        "=== YOUR JOB ===\n"
        "You will receive a competitor post (hook + caption + why-trending label). "
        "Write ONE original post in Alice's voice that borrows the STRUCTURE or "
        "ANGLE of the competitor post but applies it to Alice's audience (SMB "
        "owners using Claude). Do NOT copy phrases. Do NOT mention the competitor. "
        "Do NOT invent product claims that aren't true for Alice.\n\n"
        "Output ONLY the post body — no preamble, no quotes, no commentary. "
        "Include hashtags per the register rules. For Register A, end with a real "
        "Alice CTA (diagnostic, DM, smallbusinessaicoach.com) — not 'Reply [word]' "
        "patterns unless clearly warranted."
    )


def _user_message(post: dict) -> str:
    caption = (post.get("caption") or "").strip()
    hook = (post.get("hook_line") or "").strip()
    fmt = post.get("format_tag") or "unknown"
    creator = post.get("creator_handle") or "unknown"
    why = (post.get("why_trending") or "").strip()
    return (
        f"Competitor creator: {creator}\n"
        f"Format: {fmt}\n"
        f"Why it's working: {why or '(no label)'}\n"
        f"Hook: {hook or '(no explicit hook line)'}\n\n"
        f"Full caption:\n{caption[:2000]}\n\n"
        "Now draft Alice's version."
    )


def draft_post(channel: str, post: dict, voice_profile: str) -> str:
    if not ANTHROPIC_API_KEY:
        return "[drafter skipped: ANTHROPIC_API_KEY not set]"
    with httpx.Client(timeout=90) as client:
        r = client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": SONNET_MODEL,
                "max_tokens": 900,
                "system": _system_prompt(channel, voice_profile),
                "messages": [{"role": "user", "content": _user_message(post)}],
            },
        )
        r.raise_for_status()
        data = r.json()
        return data["content"][0]["text"].strip()


def _fetch_reddit_post(url: str) -> dict:
    """Fetch Reddit post title, body, and top comments via public JSON API."""
    try:
        json_url = url.rstrip("/") + ".json?limit=50&sort=top&depth=3"
        with httpx.Client(timeout=15, follow_redirects=True) as client:
            r = client.get(json_url, headers={"User-Agent": "content-hub/1.0"})
            r.raise_for_status()
            data = r.json()
        post_data = data[0]["data"]["children"][0]["data"]
        title = post_data.get("title", "")
        body = (post_data.get("selftext") or "").strip()[:1500]

        def _extract_comments(children: list, depth: int = 0) -> list[str]:
            results = []
            for c in children:
                cd = c.get("data", {})
                text = (cd.get("body") or "").strip()
                author = cd.get("author", "")
                score = cd.get("score", 0)
                if text and text not in ("[deleted]", "[removed]") and len(text) > 30:
                    indent = "  " * depth
                    results.append(f'{indent}u/{author} ({score} upvotes): "{text[:400]}"')
                replies = cd.get("replies") or {}
                if isinstance(replies, dict):
                    sub = replies.get("data", {}).get("children", [])
                    if sub and depth < 2:
                        results.extend(_extract_comments(sub, depth + 1))
            return results

        comments_raw = data[1]["data"]["children"]
        all_comments = _extract_comments(comments_raw)
        return {
            "title": title,
            "body": body,
            "comments": "\n\n".join(all_comments[:20]),
        }
    except Exception as e:
        log.warning("Reddit fetch failed for %s: %s", url, e)
        return {}


def draft_from_url(channel: str, url: str, voice_profile: str) -> str:
    """Fetch full Reddit post content then draft. Falls back to URL-only if fetch fails."""
    reddit_data = {}
    if "reddit.com" in url:
        reddit_data = _fetch_reddit_post(url)

    if reddit_data:
        caption_parts = []
        if reddit_data.get("body"):
            caption_parts.append(reddit_data["body"])
        if reddit_data.get("comments"):
            caption_parts.append("--- TOP COMMENTS ---\n" + reddit_data["comments"])
        stub = {
            "creator_handle": f"Reddit thread",
            "caption": "\n\n".join(caption_parts),
            "hook_line": reddit_data.get("title", ""),
            "format_tag": "discussion thread",
            "why_trending": "Real small business owners sharing what AI tasks actually work for them",
            "post_url": url,
        }
    else:
        stub = {
            "creator_handle": "(pasted URL, no caption fetched)",
            "caption": f"Source URL: {url}\n(No caption — use the URL context only, "
                       f"or skip if you can't tell what the post is about.)",
            "hook_line": "",
            "format_tag": "unknown",
            "why_trending": "",
        }
    return draft_carousel(channel, stub, voice_profile)


CAROUSEL_SYSTEM = """\
You convert a competitor post into an Alice-voice POSTER-STYLE CAROUSEL +
full feed caption using the Five-Beat Story Structure.

=== WHO ALICE IS ===
{positioning}

=== VOICE PROFILE (rules + exemplars) ===
{voice_profile}

=== FIVE-BEAT STORY STRUCTURE (mandatory) ===
Every carousel must follow this arc across its slides:
  Beat 1 — HOOK: Stop the scroll. A punchy hook formula (see below).
  Beat 2 — PROBLEM: Name the specific pain the audience lives with.
  Beat 3 — SOLUTION: Introduce Claude / Alice's method as the fix.
  Beat 4 — PROOF: One concrete result, example, or "here's what happens."
  Beat 5 — CTA: ONE of the Active CTAs below. Concrete next step.

=== SLIDE 1 HOOK RULE (non-negotiable) ===
The competitor post you receive already has a hook — either an explicit hook
line or a Reddit/post title. USE IT. Adapt the wording to Alice's voice and
audience, but keep the same structure, angle, and energy. Do NOT invent a
new hook from scratch. The hook is already there — your job is to make it
Alice's version, not to replace it with something generic.

Examples of correct adaptation:
  Source: "Your AI keeps giving generic answers because it doesn't know your business"
  Alice:  "Your AI doesn't know your business yet — that's the whole problem"

  Source: "5 automations that saved me 10 hours this week"
  Alice:  "5 Claude automations that gave me 10 hours back this week"

  Source (Reddit title): "What automations actually make money"
  Alice:  "The Claude automations that actually make money"

=== SLIDE STRUCTURE — TITLE + BODY (follow exactly) ===
Each slide has a TITLE and a BODY. Both are required on every slide.

TITLE: Bold punchy headline, 3-10 words, no period.

BODY: Rich multi-line content — give the reader something real to read.
  Use whichever format fits:
  • Bullet list  →  "→ item" per line, for tasks/tools/steps
  • Blockquote   →  "exact quote" — u/username, for real source quotes
  • Paragraph    →  short commentary or insight (2-4 lines max per block)
  • Mixed        →  list + 1-2 lines of commentary below

SLIDE BREAKDOWN (Five-Beat Story Structure):
  Slide 1 — HOOK     Title = adapted source hook. Body = 1-2 sentence setup that earns the swipe + 👇
  Slide 2 — PROBLEM  Title = the surface-level pain. Body = bullet list of what most people do + 2 lines calling it out.
  Slide 3 — SOLUTION Title = what the shift looks like. Body = bullet list of the winning approach (concrete, specific).
  Slide 4 — PROOF    Title = the key insight as a headline. Body = real verbatim quote with u/username attribution + brief commentary.
  Slide 5 — FRAMEWORK Title = the decision rule. Body = structured list (e.g. "Repetitive? → Automate it") or takeaway broken into scannable lines.
  Slide 6 — CTA      Title = emotional call to action. Body = engagement question for comments + Active CTA on its own line.

QUALITY BAR — match this level of detail:
  Slide 2 body example:
    Drafting emails
    Summarizing documents
    Brainstorming ideas
    "ChatGPT for everything"

    Useful? Yes. Transformational? Not really.
    This is the copy-paste chatbot stage — you're still doing all the stitching.

  Slide 4 body example:
    "AI saves the most time on execution tasks that repeat. Anything requiring genuine judgment still needs a human. The mistake most people make is trying to automate the judgment layer — that's where the value lives. Automate everything around it instead."
    — u/JJCookieMonster

    Read that twice.

=== ACTIVE CTAs (use ONLY these) ===
  1. Subscribe to the newsletter → smallbusinessaicoach.com
  2. DM me the word DIAGNOSTIC — I'll send the link
  3. Register for the next masterclass → smallbusinessaicoach.com
  4. Follow for weekly AI strategies for small business
  5. Comment [WORD] and I'll DM you [specific lead magnet]

=== TIKTOK TEMPLATE TYPES (pick one) ===
  Listicle | Negative | Tutorial | Breaking News

=== FOR REDDIT THREADS ===
MUST use actual thread content: quote specific comments verbatim with u/username,
use real numbers, build frameworks FROM the comments not from generic knowledge.

=== CAPTION RULES ===
First sentence matches Slide 1 hook energy. Five-Beat arc in prose. 120-200 words.
ONE Active CTA at the end. 6-10 hashtags line-broken.
Register A (LinkedIn/Instagram): professional but direct.
Register B (TikTok): lowercase, emoji-native, punchy.

=== CHANNEL ===
{channel}. Never descriptive slide titles. Never invent product claims. Do NOT copy competitor phrasing.
"""


def _extract_json(text: str) -> dict:
    s = text.strip()
    if s.startswith("```"):
        s = re.sub(r"^```(?:json)?\s*", "", s)
        s = re.sub(r"\s*```$", "", s)
    return json.loads(s)


def _carousel_system(channel: str, voice_profile: str) -> str:
    return CAROUSEL_SYSTEM.format(
        positioning=ALICE_POSITIONING.strip(),
        voice_profile=voice_profile,
        channel=channel,
    )


CAROUSEL_TOOL = {
    "name": "submit_carousel",
    "description": "Submit the Alice-voice carousel + feed caption.",
    "input_schema": {
        "type": "object",
        "required": ["slides", "caption"],
        "properties": {
            "slides": {
                "type": "array",
                "minItems": 5,
                "maxItems": 10,
                "items": {
                    "type": "object",
                    "required": ["title", "body"],
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "Bold punchy headline, 3-10 words. No trailing period.",
                        },
                        "body": {
                            "type": "string",
                            "description": "Multi-line slide body. Can include bullet lines (→ item), blockquotes (\"quoted text\" — u/username), short paragraphs, or commentary. No word limit. Leave empty string only for the cover slide.",
                        },
                    },
                },
            },
            "caption": {
                "type": "string",
                "description": "120-200 word Alice-voice feed caption. First sentence must match Slide 1 hook energy. End with one Active CTA. 6-10 hashtags with line breaks.",
            },
        },
    },
}


def _call_carousel_tool(channel: str, voice_profile: str, user_msg: str) -> dict:
    with httpx.Client(timeout=120) as client:
        r = client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": SONNET_MODEL,
                "max_tokens": 2000,
                "system": _carousel_system(channel, voice_profile),
                "tools": [CAROUSEL_TOOL],
                "tool_choice": {"type": "tool", "name": "submit_carousel"},
                "messages": [{"role": "user", "content": user_msg}],
            },
        )
        r.raise_for_status()
        data = r.json()
    tool_use = next(
        (b for b in data.get("content", []) if b.get("type") == "tool_use"),
        None,
    )
    if not tool_use:
        raise RuntimeError("carousel drafter: model did not call the tool")
    parsed = tool_use.get("input") or {}
    slides = parsed.get("slides") or []
    caption = parsed.get("caption") or ""
    cleaned = []
    for s in slides[:10]:
        if not isinstance(s, dict):
            continue
        cleaned.append({
            "title": (s.get("title") or "").strip().rstrip("."),
            "body": (s.get("body") or "").strip(),
        })
    return {"slides": cleaned, "caption": caption.strip()}


SLIDES_FROM_CAPTION_TOOL = {
    "name": "split_into_slides",
    "description": "Extract slides (title + rich body) from an Alice-voice caption.",
    "input_schema": {
        "type": "object",
        "required": ["slides"],
        "properties": {
            "slides": {
                "type": "array",
                "minItems": 6,
                "maxItems": 8,
                "items": {
                    "type": "object",
                    "required": ["title", "body"],
                    "properties": {
                        "title": {"type": "string",
                                  "description": "Bold punchy headline, 3-10 words"},
                        "body": {"type": "string",
                                 "description": "Multi-line body with bullets (→), quotes, or commentary. No word limit."},
                    },
                },
            },
        },
    },
}


def _slides_from_caption(channel: str, caption: str, voice_profile: str) -> list[dict]:
    """Fallback: the main tool returned empty slides. Ask Claude to extract
    poster-style slides from the already-valid caption.
    """
    if not caption:
        return []
    system = (
        "You extract carousel slides (title + rich body) from an Alice-voice caption "
        "for her small-business AI coach audience. "
        f"Channel: {channel}.\n\n"
        "Each slide has: TITLE (3-8 words, punchy) + BODY (multi-line, use → bullets, "
        "blockquotes, short paragraphs — no word limit). "
        "Follow the Five-Beat arc: Hook → Problem → Solution → Proof → CTA.\n\n"
        f"=== VOICE PROFILE ===\n{voice_profile}\n"
    )
    user = (
        f"CAPTION (keep this voice):\n\n{caption}\n\n"
        "Extract 6-8 slides. Slide 1 = hook. Middle slides = rich body with bullets "
        "or commentary. Last slide = CTA with a concrete Active CTA in the body: "
        "'DM me the word DIAGNOSTIC — I'll send the link', "
        "'Subscribe to the newsletter → smallbusinessaicoach.com', or "
        "'Follow for weekly AI strategies for small business'. "
        "Never leave the CTA vague."
    )
    with httpx.Client(timeout=120) as client:
        r = client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": SONNET_MODEL,
                "max_tokens": 1500,
                "system": system,
                "tools": [SLIDES_FROM_CAPTION_TOOL],
                "tool_choice": {"type": "tool", "name": "split_into_slides"},
                "messages": [{"role": "user", "content": user}],
            },
        )
        r.raise_for_status()
        data = r.json()
    tool_use = next(
        (b for b in data.get("content", []) if b.get("type") == "tool_use"),
        None,
    )
    if not tool_use:
        log.warning("slides-from-caption: no tool_use. stop_reason=%s content=%s",
                    data.get("stop_reason"), data.get("content"))
        return []
    raw_slides = (tool_use.get("input") or {}).get("slides") or []
    if not raw_slides:
        log.warning("slides-from-caption returned empty array. input=%s",
                    tool_use.get("input"))
    slides = raw_slides
    cleaned = []
    for s in slides[:10]:
        if not isinstance(s, dict):
            continue
        cleaned.append({
            "title": (s.get("title") or "").strip().rstrip("."),
            "body": (s.get("body") or "").strip(),
        })
    return cleaned


def _heuristic_slides_from_caption(caption: str) -> list[dict]:
    """Deterministic last-resort split: one slide per meaningful paragraph,
    skipping hashtag-only lines. First sentence of each paragraph = title.
    """
    if not caption:
        return []
    paragraphs = [p.strip() for p in caption.split("\n\n") if p.strip()]
    paragraphs = [p for p in paragraphs if not p.lstrip().startswith("#")
                  or "\n" in p]
    slides = []
    for p in paragraphs[:8]:
        first_line = p.split("\n", 1)[0].strip()
        first_sentence = first_line.split(". ", 1)[0].strip().rstrip(".")
        title = first_sentence[:60] if first_sentence else "slide"
        slides.append({"title": title, "body": ""})
    return slides


def draft_carousel(channel: str, post: dict, voice_profile: str) -> dict[str, Any]:
    """Return {slides: [{title, body}, ...], caption: str}.

    Primary: one tool call producing both. Fallback 1: Claude splits the
    caption in a second call. Fallback 2: deterministic paragraph split —
    guarantees non-empty slides when we have a caption at all.
    """
    if not ANTHROPIC_API_KEY:
        return {"slides": [], "caption": "[drafter skipped: ANTHROPIC_API_KEY not set]"}
    user_msg = _user_message(post)
    out = _call_carousel_tool(channel, voice_profile, user_msg)
    if not out["slides"] and out["caption"]:
        log.warning("primary drafter returned empty slides — splitting caption in a follow-up call")
        out["slides"] = _slides_from_caption(channel, out["caption"], voice_profile)
    if not out["slides"] and out["caption"]:
        log.warning("follow-up also empty — falling back to heuristic paragraph split")
        out["slides"] = _heuristic_slides_from_caption(out["caption"])
    _ensure_concrete_cta(out["slides"])
    return out


def _ensure_concrete_cta(slides: list[dict]) -> None:
    """Guarantee the final slide body has a concrete CTA.
    Safety net for when the model ships a vague CTA.
    """
    if not slides:
        return
    last = slides[-1]
    body = (last.get("body") or "").lower()
    concrete_markers = (
        "smallbusinessaicoach", "link in bio", "link in profile",
        "dm me", "dm the", "comment ", "head to", "tap the link",
    )
    if any(m in body for m in concrete_markers):
        return
    log.warning("final slide CTA is vague (%r) — appending concrete step",
                last.get("body"))
    existing = (last.get("body") or "").strip()
    last["body"] = (existing + "\n\nDM me the word DIAGNOSTIC — I'll send the link").strip()


def draft_batch(channel: str, posts: list[dict], pasted_urls: list[str],
                voice_profile: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for p in posts:
        try:
            body = draft_post(channel, p, voice_profile)
        except Exception as e:  # noqa: BLE001
            log.warning("draft failed for %s: %s", p.get("id"), e)
            body = f"[draft failed: {e}]"
        out.append({
            "source_kind": "selected",
            "source_id": p.get("id"),
            "source_url": p.get("post_url"),
            "creator": p.get("creator_handle"),
            "draft": body,
        })
    for url in pasted_urls:
        try:
            body = draft_from_url(channel, url, voice_profile)
        except Exception as e:  # noqa: BLE001
            log.warning("draft failed for pasted %s: %s", url, e)
            body = f"[draft failed: {e}]"
        out.append({
            "source_kind": "pasted",
            "source_id": None,
            "source_url": url,
            "creator": None,
            "draft": body,
        })
    return out
