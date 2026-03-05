import os
import json
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import func
import anthropic

load_dotenv()

from database import init_db, get_db
from models import Session, ToolCall, SessionStatus, ToolName, RiskLevel

app = FastAPI(title="Claude Code Operator Dashboard")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class SessionCreate(BaseModel):
    name: str
    notes: Optional[str] = None


class SessionUpdate(BaseModel):
    status: Optional[SessionStatus] = None
    ended_at: Optional[datetime] = None
    total_tokens: Optional[int] = None
    estimated_cost_usd: Optional[float] = None
    notes: Optional[str] = None


class ToolCallCreate(BaseModel):
    session_id: int
    tool_name: ToolName
    command: Optional[str] = None
    output_preview: Optional[str] = None


class ToolCallUpdate(BaseModel):
    approved: bool


class ToolCallResponse(BaseModel):
    id: int
    session_id: int
    tool_name: ToolName
    command: Optional[str]
    output_preview: Optional[str]
    risk_level: RiskLevel
    risk_reason: Optional[str]
    timestamp: datetime
    approved: bool

    class Config:
        from_attributes = True


class SessionResponse(BaseModel):
    id: int
    name: str
    status: SessionStatus
    started_at: datetime
    ended_at: Optional[datetime]
    total_tokens: int
    estimated_cost_usd: float
    notes: Optional[str]

    class Config:
        from_attributes = True


class SessionDetailResponse(SessionResponse):
    tool_calls: list[ToolCallResponse] = []


class StatsResponse(BaseModel):
    total_sessions: int
    active_sessions: int
    total_tool_calls: int
    danger_count: int
    warning_count: int
    estimated_total_cost: float


# ---------------------------------------------------------------------------
# Risk analysis
# ---------------------------------------------------------------------------

ANALYZE_PROMPT = """\
Analyze this Claude Code tool call and return JSON only — no markdown, no explanation.

Tool name: {tool_name}
Command / input:
{command}

Return exactly this shape:
{{"risk_level": "safe|warning|danger", "risk_reason": "one sentence explanation"}}

Risk classification rules:
- danger: rm -rf, DROP TABLE, DROP DATABASE, ALTER TABLE, DELETE FROM without WHERE, \
credential files (.env, id_rsa, .pem, .key), system directories (/etc, /sys, /boot)
- warning: git push --force, pip install of unknown packages, curl | bash, \
writing to config files, sudo commands
- safe: everything else
"""


def analyze_risk(tool_name: str, command: Optional[str]) -> tuple[RiskLevel, Optional[str]]:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key or api_key == "your_api_key_here":
        return _heuristic_risk(tool_name, command)

    try:
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=128,
            messages=[
                {
                    "role": "user",
                    "content": ANALYZE_PROMPT.format(
                        tool_name=tool_name,
                        command=command or "(no command provided)",
                    ),
                }
            ],
        )
        raw = message.content[0].text.strip()
        data = json.loads(raw)
        level = RiskLevel(data["risk_level"])
        reason = data.get("risk_reason")
        return level, reason
    except Exception:
        return _heuristic_risk(tool_name, command)


def _heuristic_risk(tool_name: str, command: Optional[str]) -> tuple[RiskLevel, Optional[str]]:
    cmd = (command or "").lower()

    danger_patterns = [
        "rm -rf", "drop table", "drop database", "alter table",
        "delete from", ".env", "id_rsa", ".pem", ".key",
        "/etc/", "/sys/", "/boot/",
    ]
    warning_patterns = [
        "git push --force", "git push -f", "curl | bash", "curl|bash",
        "sudo ", "pip install", "apt install", "brew install",
    ]
    config_write_patterns = [
        ".bashrc", ".zshrc", ".profile", "config.yaml", "config.json",
        "settings.py", "nginx.conf",
    ]

    for p in danger_patterns:
        if p in cmd:
            return RiskLevel.danger, f"Command contains dangerous pattern: '{p}'"

    for p in warning_patterns:
        if p in cmd:
            return RiskLevel.warning, f"Command contains elevated-risk pattern: '{p}'"

    if tool_name in ("write", "edit"):
        for p in config_write_patterns:
            if p in cmd:
                return RiskLevel.warning, f"Writing to sensitive config file: '{p}'"

    if tool_name == "read":
        return RiskLevel.safe, "Read-only operation."

    return RiskLevel.safe, "No known risk patterns detected."


# ---------------------------------------------------------------------------
# Session endpoints
# ---------------------------------------------------------------------------

@app.get("/sessions", response_model=list[SessionResponse])
def list_sessions(db: DBSession = Depends(get_db)):
    return db.query(Session).order_by(Session.started_at.desc()).all()


@app.get("/sessions/{session_id}", response_model=SessionDetailResponse)
def get_session(session_id: int, db: DBSession = Depends(get_db)):
    session = db.get(Session, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@app.post("/sessions", response_model=SessionResponse, status_code=201)
def create_session(payload: SessionCreate, db: DBSession = Depends(get_db)):
    session = Session(
        name=payload.name,
        notes=payload.notes,
        status=SessionStatus.active,
        started_at=datetime.utcnow(),
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@app.patch("/sessions/{session_id}", response_model=SessionResponse)
def update_session(session_id: int, payload: SessionUpdate, db: DBSession = Depends(get_db)):
    session = db.get(Session, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(session, field, value)

    db.commit()
    db.refresh(session)
    return session


@app.delete("/sessions/{session_id}", status_code=204)
def delete_session(session_id: int, db: DBSession = Depends(get_db)):
    session = db.get(Session, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    db.delete(session)
    db.commit()


# ---------------------------------------------------------------------------
# ToolCall endpoints
# ---------------------------------------------------------------------------

@app.post("/tool-calls", response_model=ToolCallResponse, status_code=201)
def create_tool_call(payload: ToolCallCreate, db: DBSession = Depends(get_db)):
    session = db.get(Session, payload.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    risk_level, risk_reason = analyze_risk(payload.tool_name.value, payload.command)

    tool_call = ToolCall(
        session_id=payload.session_id,
        tool_name=payload.tool_name,
        command=payload.command,
        output_preview=payload.output_preview,
        risk_level=risk_level,
        risk_reason=risk_reason,
        timestamp=datetime.utcnow(),
        approved=False,
    )
    db.add(tool_call)
    db.commit()
    db.refresh(tool_call)
    return tool_call


@app.patch("/tool-calls/{tool_call_id}", response_model=ToolCallResponse)
def update_tool_call(tool_call_id: int, payload: ToolCallUpdate, db: DBSession = Depends(get_db)):
    tool_call = db.get(ToolCall, tool_call_id)
    if not tool_call:
        raise HTTPException(status_code=404, detail="Tool call not found")
    tool_call.approved = payload.approved
    db.commit()
    db.refresh(tool_call)
    return tool_call


# ---------------------------------------------------------------------------
# Stats endpoint
# ---------------------------------------------------------------------------

@app.get("/stats", response_model=StatsResponse)
def get_stats(db: DBSession = Depends(get_db)):
    total_sessions = db.query(func.count(Session.id)).scalar()
    active_sessions = (
        db.query(func.count(Session.id))
        .filter(Session.status == SessionStatus.active)
        .scalar()
    )
    total_tool_calls = db.query(func.count(ToolCall.id)).scalar()
    danger_count = (
        db.query(func.count(ToolCall.id))
        .filter(ToolCall.risk_level == RiskLevel.danger)
        .scalar()
    )
    warning_count = (
        db.query(func.count(ToolCall.id))
        .filter(ToolCall.risk_level == RiskLevel.warning)
        .scalar()
    )
    estimated_total_cost = (
        db.query(func.coalesce(func.sum(Session.estimated_cost_usd), 0.0)).scalar()
    )

    return StatsResponse(
        total_sessions=total_sessions,
        active_sessions=active_sessions,
        total_tool_calls=total_tool_calls,
        danger_count=danger_count,
        warning_count=warning_count,
        estimated_total_cost=estimated_total_cost,
    )

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
