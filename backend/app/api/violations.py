"""Violations API with recurring risk detection."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
import uuid

from app.database import get_db
from app.auth.security import get_current_user
from app.models import (
    Violation, RecurringRisk, Task, User, Mine, Inspection,
    Observation, AIAnalysis, SeverityLevel, ViolationCategory,
    TaskStatus, TaskPriority, ComplianceStatus
)
from app.rules.engine import rule_engine
from app.audit.service import log_audit
from app.api.ws_manager import ws_manager

router = APIRouter(prefix="/violations", tags=["Violations"])


def _violation_ref():
    ts = datetime.utcnow().strftime("%Y%m%d")
    uid = str(uuid.uuid4())[:6].upper()
    return f"VIO-{ts}-{uid}"


def _task_ref():
    ts = datetime.utcnow().strftime("%Y%m%d")
    uid = str(uuid.uuid4())[:6].upper()
    return f"TSK-{ts}-{uid}"


async def _check_recurring(
    db: AsyncSession,
    mine_id: uuid.UUID,
    category: ViolationCategory,
    zone_id: Optional[uuid.UUID] = None,
) -> Optional[RecurringRisk]:
    """Check if this violation creates a recurring pattern."""
    window = datetime.utcnow() - timedelta(days=30)

    query = select(func.count(Violation.id)).where(
        and_(
            Violation.mine_id == mine_id,
            Violation.category == category,
            Violation.created_at >= window,
        )
    )
    count_result = await db.execute(query)
    count = count_result.scalar_one()

    check = rule_engine.check_recurring(
        category=category.value,
        occurrence_count=count,
        days_window=30,
    )

    if not check["is_recurring"]:
        return None

    # Check if recurring risk record already exists
    existing = await db.execute(
        select(RecurringRisk).where(
            and_(
                RecurringRisk.mine_id == mine_id,
                RecurringRisk.category == category,
                RecurringRisk.status == "active",
            )
        )
    )
    recurring = existing.scalar_one_or_none()

    if recurring:
        recurring.occurrence_count = count
        recurring.last_occurrence = datetime.utcnow()
        if count > recurring.occurrence_count:
            recurring.trend = "increasing"
        return recurring
    else:
        # Create new recurring risk
        recurring = RecurringRisk(
            mine_id=mine_id,
            zone_id=zone_id,
            category=category,
            occurrence_count=count,
            first_occurrence=window,
            last_occurrence=datetime.utcnow(),
            time_window_days=30,
            severity=SeverityLevel.HIGH,
            status="active",
            recommended_action=(
                f"RECURRING RISK: {count} {category.value} violations in 30 days. "
                "Implement systemic corrective action: safety audit, training, supervisor review."
            ),
            trend="increasing",
        )
        db.add(recurring)
        await db.flush()
        return recurring


async def _create_violation_from_observation(
    db: AsyncSession,
    observation: Observation,
    inspection: Inspection,
    analysis: AIAnalysis,
    severity: SeverityLevel,
    mine: Mine,
    current_user: User,
):
    """Create violation + task from AI analysis. Called by observations API."""
    try:
        category = ViolationCategory(analysis.category)
    except (ValueError, AttributeError):
        category = ViolationCategory.PPE

    from geoalchemy2.elements import WKTElement
    location = None
    if observation.latitude and observation.longitude:
        location = WKTElement(
            f"POINT({observation.longitude} {observation.latitude})", srid=4326
        )

    # Check recurring before creating violation
    recurring = await _check_recurring(
        db=db,
        mine_id=inspection.mine_id,
        category=category,
        zone_id=observation.zone_id,
    )

    violation = Violation(
        reference_number=_violation_ref(),
        mine_id=inspection.mine_id,
        inspection_id=inspection.id,
        observation_id=observation.id,
        category=category,
        severity=severity,
        description=observation.description,
        latitude=observation.latitude,
        longitude=observation.longitude,
        location=location,
        zone_id=observation.zone_id,
        compliance_status=ComplianceStatus.NON_COMPLIANT,
        is_recurring=recurring is not None,
        recurring_risk_id=recurring.id if recurring else None,
        photo_urls=observation.photo_urls or [],
    )
    db.add(violation)
    await db.flush()

    # Update recurring risk to link violation
    if recurring:
        violation.recurring_risk_id = recurring.id

    # Create task
    priority = rule_engine.get_task_priority(severity)
    due_date = rule_engine.get_due_date(severity)

    task = Task(
        reference_number=_task_ref(),
        mine_id=inspection.mine_id,
        violation_id=violation.id,
        title=f"[{severity.value.upper()}] {category.value} Violation — {mine.name if mine else 'Mine'}",
        description=analysis.recommended_action,
        category=category,
        priority=priority,
        status=TaskStatus.OPEN,
        due_date=due_date,
        reminder_date=datetime.utcnow() + timedelta(hours=2),
    )
    db.add(task)
    await db.flush()

    # Log audit
    await log_audit(
        db=db,
        user_id=str(current_user.id),
        action="create",
        entity_type="violation",
        entity_id=str(violation.id),
        new_value={
            "category": category.value,
            "severity": severity.value,
            "reference_number": violation.reference_number,
            "is_recurring": violation.is_recurring,
        },
    )

    # Broadcast via WebSocket for critical
    if severity == SeverityLevel.CRITICAL:
        await ws_manager.broadcast(
            {
                "type": "critical_violation",
                "violation_id": str(violation.id),
                "mine_id": str(inspection.mine_id),
                "category": category.value,
                "severity": severity.value,
                "reference_number": violation.reference_number,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    return violation, task


@router.get("")
async def list_violations(
    mine_id: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    is_recurring: Optional[bool] = Query(None),
    limit: int = Query(20, le=100),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        query = select(Violation).order_by(Violation.created_at.desc())

        if mine_id:
            query = query.where(Violation.mine_id == uuid.UUID(mine_id))
        if severity:
            query = query.where(Violation.severity == SeverityLevel(severity))
        if category:
            query = query.where(Violation.category == ViolationCategory(category))
        if is_recurring is not None:
            query = query.where(Violation.is_recurring == is_recurring)

        count_result = await db.execute(select(func.count()).select_from(query.subquery()))
        total = count_result.scalar_one()

        result = await db.execute(query.limit(limit).offset(offset))
        violations = result.scalars().all()

        return {
            "total": total,
            "items": [
                {
                    "id": str(v.id),
                    "reference_number": v.reference_number,
                    "mine_id": str(v.mine_id),
                    "category": v.category.value if v.category else None,
                    "severity": v.severity.value if v.severity else None,
                    "description": v.description,
                    "compliance_status": v.compliance_status.value if v.compliance_status else None,
                    "is_recurring": v.is_recurring,
                    "latitude": v.latitude,
                    "longitude": v.longitude,
                    "resolved_at": v.resolved_at.isoformat() if v.resolved_at else None,
                    "created_at": v.created_at.isoformat(),
                }
                for v in violations
            ],
        }
    except Exception:
        from app.services.demo_store import DEMO_VIOLATIONS
        filtered = DEMO_VIOLATIONS
        if severity:
            filtered = [v for v in filtered if v["severity"] == severity]
        if category:
            filtered = [v for v in filtered if v["category"].lower() == category.lower()]
        return {"total": len(filtered), "items": filtered[:limit]}


@router.get("/recurring")
async def list_recurring_violations(
    mine_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        query = select(RecurringRisk).where(RecurringRisk.status == "active").order_by(
            RecurringRisk.occurrence_count.desc()
        )
        if mine_id:
            query = query.where(RecurringRisk.mine_id == uuid.UUID(mine_id))

        result = await db.execute(query)
        risks = result.scalars().all()

        return {
            "total": len(risks),
            "items": [
                {
                    "id": str(r.id),
                    "mine_id": str(r.mine_id),
                    "category": r.category.value if r.category else None,
                    "occurrence_count": r.occurrence_count,
                    "first_occurrence": r.first_occurrence.isoformat() if r.first_occurrence else None,
                    "last_occurrence": r.last_occurrence.isoformat() if r.last_occurrence else None,
                    "time_window_days": r.time_window_days,
                    "severity": r.severity.value if r.severity else None,
                    "status": r.status,
                    "recommended_action": r.recommended_action,
                    "trend": r.trend,
                }
                for r in risks
            ],
        }
    except Exception:
        from app.services.demo_store import DEMO_VIOLATIONS
        recurring = [v for v in DEMO_VIOLATIONS if v.get("is_recurring")]
        return {
            "total": len(recurring),
            "items": [
                {
                    "id": v["id"],
                    "mine_id": v["mine_id"],
                    "category": v["category"],
                    "occurrence_count": 3,
                    "first_occurrence": (datetime.utcnow() - timedelta(days=20)).isoformat(),
                    "last_occurrence": v["created_at"],
                    "time_window_days": 30,
                    "severity": "high",
                    "status": "active",
                    "recommended_action": f"Recurring risk in {v['category']}. Conduct section-wide safety audit.",
                    "trend": "increasing",
                }
                for v in recurring
            ],
        }
