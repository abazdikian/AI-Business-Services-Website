#!/bin/bash
# Reddit Scout Agent — wrapper script for launchd
# Usage: ./run_reddit_scout.sh hourly | summary

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Load environment variables
if [ -f "$SCRIPT_DIR/../.env" ]; then
    export $(grep -v '^#' "$SCRIPT_DIR/../.env" | xargs)
fi

export OAUTHLIB_RELAX_TOKEN_SCOPE=1
MODE="${1:-hourly}"
/usr/bin/python3 reddit_scout.py "$MODE"
