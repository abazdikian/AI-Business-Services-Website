#!/bin/bash
# Daily Google Calendar -> hub.db sync (launchd-driven).
#
# Install:
#   chmod +x content_hub/gcal-sync.sh
#   cp content_hub/com.alice.gcal-sync.plist ~/Library/LaunchAgents/
#   launchctl load ~/Library/LaunchAgents/com.alice.gcal-sync.plist
#
# Trigger manually:
#   launchctl start com.alice.gcal-sync
#
# Logs: ~/Library/Logs/gcal-sync.{out,err}.log
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT="$(dirname "$SCRIPT_DIR")"
PYTHON="$PROJECT/.venv-hub/bin/python"
cd "$PROJECT"
exec "$PYTHON" -m content_hub.integrations.gcal --sync
