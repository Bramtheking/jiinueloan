"""Audit log helper — called from all service/CRUD functions."""
import json
from typing import Any
from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog


def log_action(
    db: Session,
    entity_type: str,
    entity_id: int,
    action: str,
    details: Any = None,
) -> AuditLog:
    """Write one immutable audit row and flush (but don't commit — caller commits)."""
    entry = AuditLog(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        details=json.dumps(details) if details is not None else None,
    )
    db.add(entry)
    db.flush()
    return entry
