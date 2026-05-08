"""Extract the hook line (first meaningful sentence) from a caption."""

import re

_SENTENCE_END = re.compile(r"(?<=[.!?])\s+|\n+")


def extract_hook(caption: str, max_chars: int = 140) -> str:
    if not caption:
        return ""
    text = caption.strip()
    # Prefer first line if it has punch
    first_line = text.split("\n", 1)[0].strip()
    if 10 <= len(first_line) <= max_chars:
        return first_line
    # Fall back to first sentence
    parts = _SENTENCE_END.split(text, maxsplit=1)
    hook = parts[0].strip() if parts else text
    if len(hook) > max_chars:
        hook = hook[: max_chars - 1].rstrip() + "…"
    return hook
