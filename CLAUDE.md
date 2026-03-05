# Claude Code Operator Dashboard

## Project Overview

This is a full-stack web application that monitors and visualizes Claude Code sessions from an operator's perspective. It provides real-time visibility into what Claude Code is doing, including tool calls, risk assessments, and token costs.

## Architecture

- **backend/** — FastAPI + SQLite (via SQLAlchemy)
- **frontend/** — React + Vite

## What It Tracks

### Sessions
Each Claude Code session is tracked with:
- Unique ID and human-readable name
- Status: `active`, `completed`, or `aborted`
- Start and end timestamps
- Total tokens consumed
- Estimated cost in USD
- Operator notes

### Tool Calls
Every tool invocation within a session is logged with:
- Tool name: `bash`, `write`, `edit`, `read`, or `other`
- The command or input passed to the tool
- A preview of the output
- Risk level: `safe`, `warning`, or `danger`
- Reason for the risk classification
- Timestamp
- Whether the call was approved by an operator

## Risk Classification

Tool calls are classified by risk:
- **safe** — Read-only operations, no side effects (e.g., `read`, `grep`, `ls`)
- **warning** — Write operations, file edits, or ambiguous commands
- **danger** — Destructive commands (`rm -rf`, `git push --force`), network calls, secret exposure, or anything with high blast radius

## Key Files

| Path | Purpose |
|---|---|
| `backend/models.py` | SQLAlchemy ORM models for Session and ToolCall |
| `backend/database.py` | SQLite engine setup, session factory, table creation |
| `backend/main.py` | FastAPI app with REST endpoints |
| `backend/requirements.txt` | Python dependencies |
| `frontend/src/` | React components for the dashboard UI |

## Development

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Environment Variables

Copy `backend/.env` and fill in your `ANTHROPIC_API_KEY` for any Claude API integrations.
