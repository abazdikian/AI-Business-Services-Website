#!/bin/bash
# Two-step pull: fast fetch (no LLM), then enrich via reparse.
# This avoids hanging on per-post Haiku calls during the Apify fetch phase.
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON="$SCRIPT_DIR/venv/bin/python"
PROJECT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT"
"$PYTHON" -m content_hub.scheduler --skip-llm
"$PYTHON" -m content_hub.scheduler --reparse
