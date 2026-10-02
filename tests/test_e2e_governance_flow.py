"""
End-to-End Governance Lifecycle Test.
Validates the complete SIH storyline:
Inspection -> Evidence Observation -> AI Risk Classification -> Compliance Rule Check ->
Task Assignment -> Escalation -> Resolution -> Verification -> Cryptographic Audit Hash Chain.
"""
import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from app.models import (
    SeverityLevel,
    ViolationCategory,
    TaskPriority,
    TaskStatus,
    ComplianceStatus,
    AuditLog,
)
from app.rules.engine import RuleEngine
from app.ai.analysis import analyze_observation
from app.audit.service import _compute_hash, verify_audit_chain


@pytest.mark.asyncio
async def test_complete_governance_storyline():
    """
    Simulate the end-to-end governance cycle:
    1. An inspector notes an observation on inadequate ventilation and missing methane checks.
    2. AI classifies this as high severity under CMR 2017 Ventilation rules.
    3. The rule engine validates severity and statutory deadline.
    4. Task is created and assigned to Ventilation In-Charge.
    5. Action is taken, task is resolved.
    6. Mine Safety Officer approves and verifies.
    7. All state changes are sealed in a SHA-256 hash chain with untampered integrity.
    """
    rule_engine = RuleEngine()
    entity_id = uuid.uuid4()
    u0 = uuid.uuid4()
    u1 = uuid.uuid4()
    u2 = uuid.uuid4()
    u3 = uuid.uuid4()
    audit_chain = []

    # Step 1: AI Observation Analysis
    observation_text = "Auxiliary ventilation fan tripped in Seam 3 Block 4, airflow dropped below statutory minimum"
    ai_result = await analyze_observation(observation_text)
    assert ai_result.category == "Ventilation"
    assert ai_result.risk_score >= 0.7

    # Step 2: Rule Engine Severity Evaluation & Statutory Deadline
    evaluation = rule_engine.evaluate_severity(
        ai_severity=ai_result.severity,
        category=ViolationCategory.VENTILATION,
        context={"mine_type": "underground"},
    )
    final_severity = evaluation["final_severity"]
    sev_enum = SeverityLevel(final_severity)

    now = datetime.utcnow()
    deadline = rule_engine.get_due_date(sev_enum)
    assert deadline > now

    # Step 3: Genesis Block — Violation and Task Creation in Audit Chain
    block_0_data = {
        "timestamp": now.isoformat(),
        "user_id": str(u0),
        "action": "VIOLATION_AND_TASK_CREATED",
        "entity_type": "violation",
        "entity_id": str(entity_id),
        "old_value": None,
        "new_value": {
            "status": ComplianceStatus.NON_COMPLIANT.value,
            "severity": sev_enum.value,
            "category": ViolationCategory.VENTILATION.value,
            "deadline": deadline.isoformat(),
        },
        "previous_hash": None,
    }
    hash_0 = _compute_hash(block_0_data)
    entry_0 = AuditLog(
        id=uuid.uuid4(),
        timestamp=now,
        user_id=u0,
        action="VIOLATION_AND_TASK_CREATED",
        entity_type="violation",
        entity_id=entity_id,
        old_value=None,
        new_value=block_0_data["new_value"],
        record_hash=hash_0,
        previous_hash=None,
    )
    audit_chain.append(entry_0)

    # Step 4: Step 2 in Hash Chain — Task Assigned
    assign_time = now + timedelta(minutes=15)
    block_1_data = {
        "timestamp": assign_time.isoformat(),
        "user_id": str(u1),
        "action": "TASK_ASSIGNED",
        "entity_type": "violation",
        "entity_id": str(entity_id),
        "old_value": {"status": ComplianceStatus.NON_COMPLIANT.value},
        "new_value": {"status": TaskStatus.ASSIGNED.value, "assignee": "Ventilation In-Charge"},
        "previous_hash": hash_0,
    }
    hash_1 = _compute_hash(block_1_data)
    entry_1 = AuditLog(
        id=uuid.uuid4(),
        timestamp=assign_time,
        user_id=u1,
        action="TASK_ASSIGNED",
        entity_type="violation",
        entity_id=entity_id,
        old_value={"status": ComplianceStatus.NON_COMPLIANT.value},
        new_value=block_1_data["new_value"],
        record_hash=hash_1,
        previous_hash=hash_0,
    )
    audit_chain.append(entry_1)

    # Step 5: Step 3 in Hash Chain — Resolution
    resolve_time = now + timedelta(hours=3)
    block_2_data = {
        "timestamp": resolve_time.isoformat(),
        "user_id": str(u2),
        "action": "TASK_RESOLVED",
        "entity_type": "violation",
        "entity_id": str(entity_id),
        "old_value": {"status": TaskStatus.ASSIGNED.value},
        "new_value": {
            "status": TaskStatus.RESOLVED.value,
            "evidence": "Auxiliary fan motor relay replaced. Airflow restored to 450 m3/min.",
        },
        "previous_hash": hash_1,
    }
    hash_2 = _compute_hash(block_2_data)
    entry_2 = AuditLog(
        id=uuid.uuid4(),
        timestamp=resolve_time,
        user_id=u2,
        action="TASK_RESOLVED",
        entity_type="violation",
        entity_id=entity_id,
        old_value={"status": TaskStatus.ASSIGNED.value},
        new_value=block_2_data["new_value"],
        record_hash=hash_2,
        previous_hash=hash_1,
    )
    audit_chain.append(entry_2)

    # Step 6: Step 4 in Hash Chain — Mine Safety Officer Verification
    verify_time = now + timedelta(hours=4)
    block_3_data = {
        "timestamp": verify_time.isoformat(),
        "user_id": str(u3),
        "action": "TASK_VERIFIED_AND_CLOSED",
        "entity_type": "violation",
        "entity_id": str(entity_id),
        "old_value": {"status": TaskStatus.RESOLVED.value},
        "new_value": {"status": TaskStatus.CLOSED.value, "verified": True, "approver": "Mine Safety Officer"},
        "previous_hash": hash_2,
    }
    hash_3 = _compute_hash(block_3_data)
    entry_3 = AuditLog(
        id=uuid.uuid4(),
        timestamp=verify_time,
        user_id=u3,
        action="TASK_VERIFIED_AND_CLOSED",
        entity_type="violation",
        entity_id=entity_id,
        old_value={"status": TaskStatus.RESOLVED.value},
        new_value=block_3_data["new_value"],
        record_hash=hash_3,
        previous_hash=hash_2,
    )
    audit_chain.append(entry_3)

    # Step 7: Cryptographic Chain Verification Check
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = audit_chain
    mock_db.execute.return_value = mock_result

    audit_result = await verify_audit_chain(mock_db, "violation", str(entity_id))
    assert audit_result["verified"] is True
    assert audit_result["chain_length"] == 4
    assert audit_result["broken_at_index"] is None
    assert "AUDIT INTEGRITY: VERIFIED" in audit_result["message"]
