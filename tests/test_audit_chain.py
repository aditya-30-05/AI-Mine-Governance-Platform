"""Unit tests for SHA-256 cryptographic audit chain and tamper detection."""
import pytest
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from app.audit.service import _compute_hash, log_audit, verify_audit_chain
from app.models import AuditLog


def test_compute_hash_deterministic():
    """Verify that identical record payloads produce the exact same SHA-256 hash."""
    user_id = str(uuid.uuid4())
    record1 = {
        "timestamp": "2026-10-02T10:00:00",
        "action": "TASK_CREATED",
        "entity_type": "task",
        "entity_id": "123e4567-e89b-12d3-a456-426614174000",
        "old_value": None,
        "new_value": {"status": "assigned"},
        "previous_hash": None,
        "user_id": user_id,
    }
    record2 = record1.copy()
    assert _compute_hash(record1) == _compute_hash(record2)
    assert len(_compute_hash(record1)) == 64  # SHA-256 produces 64 hex characters


def test_compute_hash_detects_modification():
    """Verify that any tampering in payload alters the SHA-256 hash."""
    record_clean = {
        "timestamp": "2026-10-02T10:00:00",
        "action": "TASK_RESOLVED",
        "entity_type": "task",
        "entity_id": "123e4567-e89b-12d3-a456-426614174000",
        "old_value": {"status": "in_progress"},
        "new_value": {"status": "resolved", "note": "Replaced ventilation fan"},
        "previous_hash": "a" * 64,
        "user_id": str(uuid.uuid4()),
    }
    record_tampered = record_clean.copy()
    record_tampered["new_value"] = {"status": "resolved", "note": "Malicious altered note"}

    assert _compute_hash(record_clean) != _compute_hash(record_tampered)


@pytest.mark.asyncio
async def test_audit_chain_verification_valid():
    """Verify that an untampered hash chain passes verification."""
    entity_id = uuid.uuid4()
    user1_id = uuid.uuid4()
    user2_id = uuid.uuid4()
    now1 = datetime(2026, 10, 2, 10, 0, 0)
    now2 = datetime(2026, 10, 2, 11, 0, 0)

    # Genesis block
    data1 = {
        "timestamp": now1.isoformat(),
        "user_id": str(user1_id),
        "action": "VIOLATION_REPORTED",
        "entity_type": "violation",
        "entity_id": str(entity_id),
        "old_value": None,
        "new_value": {"severity": "critical", "category": "ventilation"},
        "previous_hash": None,
    }
    hash1 = _compute_hash(data1)
    entry1 = AuditLog(
        id=uuid.uuid4(),
        timestamp=now1,
        user_id=user1_id,
        action="VIOLATION_REPORTED",
        entity_type="violation",
        entity_id=entity_id,
        old_value=None,
        new_value={"severity": "critical", "category": "ventilation"},
        record_hash=hash1,
        previous_hash=None,
    )

    # Second block pointing to Genesis block
    data2 = {
        "timestamp": now2.isoformat(),
        "user_id": str(user2_id),
        "action": "VIOLATION_ESCALATED",
        "entity_type": "violation",
        "entity_id": str(entity_id),
        "old_value": {"status": "open"},
        "new_value": {"status": "escalated"},
        "previous_hash": hash1,
    }
    hash2 = _compute_hash(data2)
    entry2 = AuditLog(
        id=uuid.uuid4(),
        timestamp=now2,
        user_id=user2_id,
        action="VIOLATION_ESCALATED",
        entity_type="violation",
        entity_id=entity_id,
        old_value={"status": "open"},
        new_value={"status": "escalated"},
        record_hash=hash2,
        previous_hash=hash1,
    )

    # Mock DB session returning entries
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [entry1, entry2]
    mock_db.execute.return_value = mock_result

    verification = await verify_audit_chain(mock_db, "violation", str(entity_id))
    assert verification["verified"] is True
    assert verification["chain_length"] == 2
    assert "VERIFIED" in verification["message"]


@pytest.mark.asyncio
async def test_audit_chain_verification_detects_tampering():
    """Verify that tampering with an entry's state is detected and flags exact broken index."""
    entity_id = uuid.uuid4()
    user_id = uuid.uuid4()
    now1 = datetime(2026, 10, 2, 10, 0, 0)
    data1 = {
        "timestamp": now1.isoformat(),
        "user_id": str(user_id),
        "action": "TASK_CREATED",
        "entity_type": "task",
        "entity_id": str(entity_id),
        "old_value": None,
        "new_value": {"priority": "critical"},
        "previous_hash": None,
    }
    hash1 = _compute_hash(data1)

    # Malicious actor modified new_value without updating hash
    entry_tampered = AuditLog(
        id=uuid.uuid4(),
        timestamp=now1,
        user_id=user_id,
        action="TASK_CREATED",
        entity_type="task",
        entity_id=entity_id,
        old_value=None,
        new_value={"priority": "low"},  # TAMPERED from critical to low
        record_hash=hash1,  # original hash preserved
        previous_hash=None,
    )

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [entry_tampered]
    mock_db.execute.return_value = mock_result

    verification = await verify_audit_chain(mock_db, "task", str(entity_id))
    assert verification["verified"] is False
    assert verification["broken_at_index"] == 0
    assert "INTEGRITY VIOLATION" in verification["message"]
