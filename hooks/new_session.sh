#!/usr/bin/env bash
# Usage: bash new_session.sh "Fix: login page"
# Creates a new dashboard session and saves its id to ~/.claude_dashboard_session.

set -euo pipefail

API_BASE="http://localhost:8000"
SESSION_FILE="$HOME/.claude_dashboard_session"

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 \"Session name\"" >&2
  exit 1
fi

NAME="$1"

RESPONSE=$(curl -sf -X POST "$API_BASE/sessions" \
  -H "Content-Type: application/json" \
  -d "{\"name\": $(echo -n "$NAME" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')}" \
)

if [[ -z "$RESPONSE" ]]; then
  echo "Error: backend did not respond. Is the dashboard running?" >&2
  exit 1
fi

SESSION_ID=$(echo "$RESPONSE" | python3 -c 'import json,sys; print(json.loads(sys.stdin.read())["id"])')

echo "$SESSION_ID" > "$SESSION_FILE"
echo "Session created: id=$SESSION_ID  name=\"$NAME\""
echo "Saved to $SESSION_FILE"
