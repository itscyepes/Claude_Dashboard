#!/usr/bin/env python3
"""
UserPromptSubmit hook — touches last_seen_at on the active dashboard session
so the operator can see the session is still live. Sessions are never auto-completed
by this hook; use close_session.sh or new_session.sh to end a session explicitly.

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


def _get(path: str):
    req = urllib.request.Request(f"{API_BASE}{path}", method="GET")
    with urllib.request.urlopen(req, timeout=3) as resp:
        return json.loads(resp.read())


def get_or_create_session() -> int:
    """Return an active session id, creating an auto session if none exists."""
    # Check session file first
    try:
        with open(SESSION_FILE) as f:
            sid = int(f.read().strip())
        session = _get(f"/sessions/{sid}")
        if session.get("status") == "active":
            return sid
    except Exception:
        pass

    # Scan for any active session on the backend
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


def main():
    # Drain stdin (Claude Code always pipes data even if we don't need it)
    try:
        sys.stdin.read()
    except Exception:
        pass

    try:
        sid = get_or_create_session()
        _post(f"/sessions/{sid}/ping", {})
    except (urllib.error.URLError, OSError):
        pass
    except Exception:
        pass

    sys.exit(0)


if __name__ == "__main__":
    main()
