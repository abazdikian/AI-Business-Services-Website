"""Claude Sonnet: transcript → deck sections via tool-use.

Produces a compact structure for the Slides builder: a video summary,
Alice's angle, and 5-8 sections with title + bullets + optional pull-quote.

Uses Anthropic tool-use so structured output is enforced by the API —
avoids fragile JSON parsing of raw model text.
"""

import json
import logging
from typing import Any

import httpx

from ..config import ANTHROPIC_API_KEY

log = logging.getLogger(__name__)
SONNET_MODEL = "claude-sonnet-4-6"

SYSTEM = """\
You turn YouTube transcripts into a presenter deck that a small-business AI
coach (Alice) can talk THROUGH on camera while responding to the video.

Alice's audience: solopreneurs / small-team founders using Claude as a
strategist and operator. She teaches AI strategy for non-technical people.

Rules:
- 5 to 8 sections, ordered the way the video flows.
- Titles must be crisp and speakable — no clickbait, no emojis.
- Bullets are talking points Alice could riff on, NOT verbatim transcript.
- Do NOT invent claims not supported by the transcript.
- Quotes must appear verbatim in the transcript (empty string if nothing stands out).
"""

DECK_TOOL = {
    "name": "submit_deck_sections",
    "description": "Submit the structured deck sections for Alice's talking deck.",
    "input_schema": {
        "type": "object",
        "required": ["video_summary", "her_angle", "sections"],
        "properties": {
            "video_summary": {
                "type": "string",
                "description": "1-2 sentences — what the video is actually about",
            },
            "her_angle": {
                "type": "string",
                "description": "1 sentence — how Alice should frame her response for SMB owners",
            },
            "sections": {
                "type": "array",
                "minItems": 5,
                "maxItems": 8,
                "items": {
                    "type": "object",
                    "required": ["title", "bullets"],
                    "properties": {
                        "title": {"type": "string",
                                  "description": "4-7 word slide title"},
                        "bullets": {
                            "type": "array",
                            "minItems": 3,
                            "maxItems": 5,
                            "items": {"type": "string",
                                      "description": "short bullet, under 12 words"},
                        },
                        "quote": {"type": "string",
                                  "description": "optional verbatim pull-quote, or empty string"},
                    },
                },
            },
        },
    },
}


def _repair_sections_string(s: str) -> list:
    """Claude sometimes serializes arrays as JSON strings instead of passing
    a native array through tool_use. Try a few repair strategies before giving up.
    """
    import ast
    # 1. straight JSON
    try:
        out = json.loads(s)
        return out if isinstance(out, list) else []
    except json.JSONDecodeError:
        pass
    # 2. collapse double-doubled quotes `""x""` → `"x"`
    try:
        out = json.loads(s.replace('""', '"'))
        return out if isinstance(out, list) else []
    except json.JSONDecodeError:
        pass
    # 3. python-literal eval (handles single quotes + ' inside strings)
    try:
        out = ast.literal_eval(s)
        return out if isinstance(out, list) else []
    except (ValueError, SyntaxError):
        pass
    log.warning("could not repair sections string; first 200 chars: %r", s[:200])
    return []


def summarize_transcript(title: str, creator: str, transcript_text: str) -> dict[str, Any]:
    if not ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY not set")
    snippet = transcript_text[:18000]
    user = (
        f"Video title: {title}\n"
        f"Creator: {creator}\n\n"
        f"TRANSCRIPT:\n{snippet}\n\n"
        "Call submit_deck_sections with the structured deck now."
    )
    with httpx.Client(timeout=180) as client:
        r = client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": SONNET_MODEL,
                "max_tokens": 3000,
                "system": SYSTEM,
                "tools": [DECK_TOOL],
                "tool_choice": {"type": "tool", "name": "submit_deck_sections"},
                "messages": [{"role": "user", "content": user}],
            },
        )
        r.raise_for_status()
        body = r.json()
    tool_use = next(
        (b for b in body.get("content", []) if b.get("type") == "tool_use"),
        None,
    )
    if not tool_use:
        log.error("no tool_use in response; stop_reason=%s", body.get("stop_reason"))
        raise RuntimeError("deck sections: model did not call the tool")
    parsed = tool_use.get("input") or {}

    # Defensive: Claude occasionally returns array fields as JSON-encoded strings.
    sections = parsed.get("sections")
    if isinstance(sections, str):
        parsed["sections"] = _repair_sections_string(sections)

    # Normalize each section: ensure dict + bullets is a list
    clean_sections = []
    for s in parsed.get("sections") or []:
        if isinstance(s, str):
            clean_sections.append({"title": s, "bullets": [], "quote": ""})
            continue
        if not isinstance(s, dict):
            continue
        bullets = s.get("bullets") or []
        if isinstance(bullets, str):
            try:
                bullets = json.loads(bullets)
            except json.JSONDecodeError:
                bullets = [bullets]
        clean_sections.append({
            "title": (s.get("title") or "").strip(),
            "bullets": [str(b).strip() for b in bullets if b],
            "quote": (s.get("quote") or "").strip().strip('"'),
        })
    parsed["sections"] = clean_sections
    return parsed
