#!/usr/bin/env bash
# Manually marks the current dashboard session as completed.
# Usage: bash close_session.sh

set -euo pipefail

HOOKS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=hooks/.env
[[ -f "$HOOKS_DIR/.env" ]] && source "$HOOKS_DIR/.env"

API_BASE="https://claudedashboard-production.up.railway.app"
SESSION_FILE="$HOME/.claude_dashboard_session"
AUTH_HEADER="X-API-Key: ${DASHBOARD_API_KEY:-}"

if [[ ! -f "$SESSION_FILE" ]]; then
  echo "No active session file found at $SESSION_FILE" >&2
  exit 1
fi

SESSION_ID=$(cat "$SESSION_FILE")

if [[ -z "$SESSION_ID" ]]; then
  echo "Session file is empty." >&2
  exit 1
fi

ENDED_AT=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

RESPONSE=$(curl -sf -X PATCH "$API_BASE/sessions/$SESSION_ID" \
  -H "Content-Type: application/json" \
  -H "$AUTH_HEADER" \
  -d "{\"status\": \"completed\", \"ended_at\": \"$ENDED_AT\"}" \
)

if [[ -z "$RESPONSE" ]]; then
  echo "Error: backend did not respond. Is the dashboard running?" >&2
  exit 1
fi

rm -f "$SESSION_FILE"
echo "Session $SESSION_ID marked as completed."
