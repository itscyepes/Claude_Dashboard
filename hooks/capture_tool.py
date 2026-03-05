#!/usr/bin/env python3
"""
PreToolUse hook — captures every Claude Code tool call to the operator dashboard.
Claude Code pipes JSON to stdin; we POST to the backend silently.
Exit 0 always so Claude Code is never blocked.
"""

import json
import sys
import os
import urllib.request
import urllib.error
from datetime import datetime

API_BASE = "https://claudedashboard-production.up.railway.app"
SESSION_FILE = os.path.expanduser("~/.claude_dashboard_session")

# Load API key from hooks/.env if not already in environment
_ENV_FILE = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(_ENV_FILE):
    with open(_ENV_FILE) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())

API_KEY = os.environ.get("DASHBOARD_API_KEY", "")


def _auth_headers() -> dict:
    h = {"Content-Type": "application/json"}
    if API_KEY:
        h["X-API-Key"] = API_KEY
    return h


def _post(path: str, payload: dict) -> dict:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{API_BASE}{path}",
        data=data,
        headers=_auth_headers(),
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=3) as resp:
        return json.loads(resp.read())


def _patch(path: str, payload: dict) -> dict:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{API_BASE}{path}",
        data=data,
        headers=_auth_headers(),
        method="PATCH",
    )
    with urllib.request.urlopen(req, timeout=3) as resp:
        return json.loads(resp.read())


def _get(path: str) -> dict | list:
    req = urllib.request.Request(f"{API_BASE}{path}", method="GET")
    with urllib.request.urlopen(req, timeout=3) as resp:
        return json.loads(resp.read())


def get_or_create_session() -> int:
    """Return the current active session id, creating one if needed."""
    # Try reading from temp file first
    try:
        with open(SESSION_FILE) as f:
            sid = int(f.read().strip())
        # Verify it still exists and is active
        session = _get(f"/sessions/{sid}")
        if session.get("status") == "active":
            return sid
    except Exception:
        pass

    # Look for any active session on the backend
    try:
        sessions = _get("/sessions")
        for s in sessions:
            if s.get("status") == "active":
                sid = s["id"]
                with open(SESSION_FILE, "w") as f:
                    f.write(str(sid))
                return sid
    except Exception:
        pass

    # Create a new auto session
    name = "Auto: " + datetime.now().strftime("%Y-%m-%d %H:%M")
    session = _post("/sessions", {"name": name, "notes": "Created automatically by hook"})
    sid = session["id"]
    with open(SESSION_FILE, "w") as f:
        f.write(str(sid))
    return sid


def extract_tool_info(hook_data: dict) -> tuple[str, str | None]:
    """
    Parse Claude Code PreToolUse hook payload.

    Exact schema from Claude Code:
    {
        "session_id":      "uuid",
        "tool_name":       "Bash" | "Write" | "Edit" | "Read" | ...,  # capitalized
        "tool_input":      { "command": "...", "description": "..." },
        "tool_use_id":     "...",
        "hook_event_name": "PreToolUse",
        "cwd":             "/path/to/cwd"
    }
    """
    # tool_name is at the top level; normalize capitalized names to lowercase enum values
    raw_tool = hook_data.get("tool_name", "other").lower()
    name_map = {"bash": "bash", "write": "write", "edit": "edit", "read": "read"}
    tool_name = name_map.get(raw_tool, "other")

    tool_input = hook_data.get("tool_input", {})

    # Extract the most useful command string per tool type
    if tool_name == "bash":
        command = tool_input.get("command") or tool_input.get("cmd")
        # Append description if present and different from the command
        description = tool_input.get("description", "")
        if description and description != command:
            command = f"{command}  # {description}" if command else description
    elif tool_name in ("write", "edit"):
        path = tool_input.get("file_path") or tool_input.get("path", "")
        content_preview = str(tool_input.get("content", ""))[:80]
        command = path + (f"\n{content_preview}" if content_preview else "")
    elif tool_name == "read":
        command = tool_input.get("file_path") or tool_input.get("path")
    else:
        # Serialize whatever is there
        command = json.dumps(tool_input)[:200] if tool_input else None

    return tool_name, command


def main():
    try:
        raw = sys.stdin.read()
        hook_data = json.loads(raw) if raw.strip() else {}
    except Exception:
        hook_data = {}

    try:
        session_id = get_or_create_session()
        tool_name, command = extract_tool_info(hook_data)

        _post("/tool-calls", {
            "session_id": session_id,
            "tool_name": tool_name,
            "command": command,
            "output_preview": None,
        })
    except (urllib.error.URLError, OSError):
        # Backend is down — silently continue
        pass
    except Exception:
        # Any other error — never block Claude Code
        pass

    sys.exit(0)


if __name__ == "__main__":
    main()
