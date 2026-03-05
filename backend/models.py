from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from database import Base
import enum
from datetime import datetime


class SessionStatus(str, enum.Enum):
    active = "active"
    completed = "completed"
    aborted = "aborted"


class ToolName(str, enum.Enum):
    bash = "bash"
    write = "write"
    edit = "edit"
    read = "read"
    other = "other"


class RiskLevel(str, enum.Enum):
    safe = "safe"
    warning = "warning"
    danger = "danger"


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    status = Column(Enum(SessionStatus), nullable=False, default=SessionStatus.active)
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    last_seen_at = Column(DateTime, nullable=True)
    total_tokens = Column(Integer, nullable=False, default=0)
    estimated_cost_usd = Column(Float, nullable=False, default=0.0)
    notes = Column(String, nullable=True)

    tool_calls = relationship("ToolCall", back_populates="session", cascade="all, delete-orphan")


class ToolCall(Base):
    __tablename__ = "tool_calls"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    tool_name = Column(Enum(ToolName), nullable=False)
    command = Column(String, nullable=True)
    output_preview = Column(String, nullable=True)
    risk_level = Column(Enum(RiskLevel), nullable=False, default=RiskLevel.safe)
    risk_reason = Column(String, nullable=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    approved = Column(Boolean, nullable=False, default=False)

    session = relationship("Session", back_populates="tool_calls")
