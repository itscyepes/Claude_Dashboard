#!/usr/bin/env bash
# Usage: bash new_session.sh "Fix: login page"
# Creates a new dashboard session and saves its id to ~/.claude_dashboard_session.

set -euo pipefail

HOOKS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=hooks/.env
[[ -f "$HOOKS_DIR/.env" ]] && source "$HOOKS_DIR/.env"

API_BASE="https://claudedashboard-production.up.railway.app"
SESSION_FILE="$HOME/.claude_dashboard_session"
AUTH_HEADER="X-API-Key: ${DASHBOARD_API_KEY:-}"

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 \"Session name\"" >&2
  exit 1
fi

NAME="$1"

# Close the previous session if one is tracked
if [[ -f "$SESSION_FILE" ]]; then
  PREV_ID=$(cat "$SESSION_FILE")
  if [[ -n "$PREV_ID" ]]; then
    ENDED_AT=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    curl -sf -X PATCH "$API_BASE/sessions/$PREV_ID" \
      -H "Content-Type: application/json" \
      -H "$AUTH_HEADER" \
      -d "{\"status\": \"completed\", \"ended_at\": \"$ENDED_AT\"}" \
      > /dev/null 2>&1 || true
    echo "Closed previous session: id=$PREV_ID"
  fi
fi

RESPONSE=$(curl -sf -X POST "$API_BASE/sessions" \
  -H "Content-Type: application/json" \
  -H "$AUTH_HEADER" \
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
