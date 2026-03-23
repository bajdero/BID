"""
src/api/models/audit.py
AuditLog ORM model — immutable record of state transitions and metadata changes.

Every state change or metadata update performed by the API is appended here.
Records are never modified or deleted by application code (append-only).
`user_id` is nullable for Phase-1 (auth not yet implemented); populated in P1-04.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.api.models.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    folder: Mapped[str] = mapped_column(String(512), nullable=False)
    filename: Mapped[str] = mapped_column(String(512), nullable=False)

    # Action type — one of: "state_change", "metadata_update", "export", "conflict_resolve"
    action: Mapped[str] = mapped_column(String(64), nullable=False)

    # Before/after values serialised as strings (state name, JSON snippet, etc.)
    old_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_value: Mapped[str | None] = mapped_column(Text, nullable=True)

    timestamp: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, index=True)

    # Populated in P1-04 once JWT auth is implemented.
    user_id: Mapped[str | None] = mapped_column(String(128), nullable=True)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<AuditLog {self.project_id}:{self.folder}/{self.filename}"
            f" action={self.action!r} at {self.timestamp}>"
        )
