"""Audit service: SHA-256 hash chain for tamper-evident records."""
import hashlib
import json
from datetime import datetime
from typing import Optional, Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.models import AuditLog


def _compute_hash(record: Dict[str, Any]) -> str:
    """Compute SHA-256 hash of a record dict."""
    canonical = json.dumps(record, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()


async def log_audit(
    db: AsyncSession,
    action: str,
    entity_type: str,
    user_id: Optional[str] = None,
    entity_id: Optional[str] = None,
    old_value: Optional[Dict] = None,
    new_value: Optional[Dict] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> AuditLog:
    """Create a tamper-evident audit log entry."""
    # Get previous hash for this entity chain
    previous_hash = None
    if entity_id:
        result = await db.execute(
            select(AuditLog)
            .where(AuditLog.entity_type == entity_type, AuditLog.entity_id == entity_id)
            .order_by(desc(AuditLog.timestamp))
            .limit(1)
        )
        prev = result.scalar_one_or_none()
        if prev:
            previous_hash = prev.record_hash

    now = datetime.utcnow()
    record_data = {
        "timestamp": now.isoformat(),
        "user_id": user_id,
        "action": action,
        "entity_type": entity_type,
        "entity_id": str(entity_id) if entity_id else None,
        "old_value": old_value,
        "new_value": new_value,
        "previous_hash": previous_hash,
    }
    record_hash = _compute_hash(record_data)

    audit = AuditLog(
        timestamp=now,
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        old_value=old_value,
        new_value=new_value,
        ip_address=ip_address,
        user_agent=user_agent,
        record_hash=record_hash,
        previous_hash=previous_hash,
    )
    db.add(audit)
    # Don't commit here — let the caller's transaction handle it
    return audit


async def verify_audit_chain(
    db: AsyncSession, entity_type: str, entity_id: str
) -> Dict[str, Any]:
    """Verify the integrity of the audit hash chain for an entity."""
    result = await db.execute(
        select(AuditLog)
        .where(AuditLog.entity_type == entity_type, AuditLog.entity_id == entity_id)
        .order_by(AuditLog.timestamp)
    )
    entries = result.scalars().all()

    if not entries:
        return {"verified": True, "chain_length": 0, "message": "No audit records"}

    chain_valid = True
    broken_at = None

    for i, entry in enumerate(entries):
        # Recompute hash
        record_data = {
            "timestamp": entry.timestamp.isoformat(),
            "user_id": str(entry.user_id) if entry.user_id else None,
            "action": entry.action,
            "entity_type": entry.entity_type,
            "entity_id": str(entry.entity_id) if entry.entity_id else None,
            "old_value": entry.old_value,
            "new_value": entry.new_value,
            "previous_hash": entry.previous_hash,
        }
        expected_hash = _compute_hash(record_data)
        if expected_hash != entry.record_hash:
            chain_valid = False
            broken_at = i
            break

    return {
        "verified": chain_valid,
        "chain_length": len(entries),
        "broken_at_index": broken_at,
        "message": "AUDIT INTEGRITY: VERIFIED" if chain_valid else f"INTEGRITY VIOLATION at entry {broken_at}",
    }
