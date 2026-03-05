#!/usr/bin/env python3
"""
Stop hook — marks the current dashboard session as completed when Claude Code exits.
"""

import json
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone
import os

API_BASE = "https://claudedashboard-production.up.railway.app"
SESSION_FILE = os.path.expanduser("~/.claude_dashboard_session")


def _patch(path: str, payload: dict) -> dict:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{API_BASE}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="PATCH",
    )
    with urllib.request.urlopen(req, timeout=3) as resp:
        return json.loads(resp.read())


def main():
    try:
        with open(SESSION_FILE) as f:
            sid = int(f.read().strip())
    except Exception:
        sys.exit(0)

    try:
        ended_at = datetime.now(timezone.utc).isoformat()
        _patch(f"/sessions/{sid}", {
            "status": "completed",
            "ended_at": ended_at,
        })
    except (urllib.error.URLError, OSError):
        # Backend is down — silently continue
        pass
    except Exception:
        pass

    # Clean up session file regardless
    try:
        os.remove(SESSION_FILE)
    except OSError:
        pass

    sys.exit(0)


if __name__ == "__main__":
    main()
