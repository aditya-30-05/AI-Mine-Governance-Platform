"""Observations API — capture with AI analysis trigger."""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid
import os
import aiofiles

from app.database import get_db
from app.auth.security import get_current_user
from app.models import (
    Observation, Inspection, AIAnalysis, Violation, Task, User,
    SeverityLevel, ViolationCategory, TaskStatus
)
from app.ai.analysis import ai_service
from app.rules.engine import rule_engine
from app.audit.service import log_audit
from app.api.violations import _create_violation_from_observation
from app.config import settings

router = APIRouter(prefix="/observations", tags=["Observations"])


class ObservationCreate(BaseModel):
    inspection_id: str
    zone_id: Optional[str] = None
    description: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    accuracy_meters: Optional[float] = None
    category: Optional[str] = None
    client_id: Optional[str] = None
    captured_at: Optional[datetime] = None


@router.post("", status_code=201)
async def create_observation(
    data: ObservationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create observation → trigger AI analysis → apply rules → create violation + task if needed.
    """
    # Validate inspection
    insp_result = await db.execute(
        select(Inspection).where(Inspection.id == uuid.UUID(data.inspection_id))
    )
    inspection = insp_result.scalar_one_or_none()
    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection not found")

    from geoalchemy2.elements import WKTElement
    location = None
    if data.latitude and data.longitude:
        location = WKTElement(f"POINT({data.longitude} {data.latitude})", srid=4326)

    observation = Observation(
        inspection_id=uuid.UUID(data.inspection_id),
        zone_id=uuid.UUID(data.zone_id) if data.zone_id else None,
        description=data.description,
        latitude=data.latitude,
        longitude=data.longitude,
        accuracy_meters=data.accuracy_meters,
        location=location,
        client_id=data.client_id,
        captured_at=data.captured_at or datetime.utcnow(),
    )
    db.add(observation)
    await db.flush()

    # AI Analysis
    mine_result = await db.execute(select(__import__('app.models', fromlist=['Mine']).Mine).where(
        __import__('app.models', fromlist=['Mine']).Mine.id == inspection.mine_id
    ))
    mine = mine_result.scalar_one_or_none()

    ai_result = await ai_service.analyze_observation(
        description=data.description,
        mine_name=mine.name if mine else "Unknown",
        zone_name="",
        photo_count=0,
        gps=f"{data.latitude},{data.longitude}" if data.latitude else "Not captured",
    )

    # Rule engine validation
    rule_result = rule_engine.evaluate_severity(
        ai_severity=ai_result.severity,
        category=ai_result.category,
        context={"mine_type": mine.mine_type if mine else "opencast"},
    )

    final_severity = SeverityLevel(rule_result["final_severity"])

    # Save AI analysis
    analysis = AIAnalysis(
        observation_id=observation.id,
        input_text=data.description,
        model_used=ai_result.model_used,
        is_demo_fallback=ai_result.is_demo_fallback,
        category=ai_result.category,
        severity=final_severity,
        risk_score=ai_result.risk_score,
        confidence=ai_result.confidence,
        explanation=ai_result.explanation,
        recommended_action=ai_result.recommended_action,
        raw_response=ai_result.raw_response,
        rule_adjusted=rule_result["adjusted"],
        rule_adjustment_reason="; ".join(rule_result["adjustments"]) if rule_result["adjustments"] else None,
    )
    db.add(analysis)
    await db.flush()

    # Link analysis to observation
    observation.ai_analysis_id = analysis.id
    try:
        observation.category = ViolationCategory(ai_result.category)
    except ValueError:
        pass

    # Create violation and task if severity warrants
    violation_id = None
    task_id = None
    if final_severity in [SeverityLevel.CRITICAL, SeverityLevel.HIGH, SeverityLevel.MEDIUM]:
        violation, task = await _create_violation_from_observation(
            db=db,
            observation=observation,
            inspection=inspection,
            analysis=analysis,
            severity=final_severity,
            mine=mine,
            current_user=current_user,
        )
        violation_id = str(violation.id) if violation else None
        task_id = str(task.id) if task else None

    await log_audit(
        db=db,
        user_id=str(current_user.id),
        action="create",
        entity_type="observation",
        entity_id=str(observation.id),
        new_value={
            "description": data.description[:100],
            "severity": final_severity.value,
            "category": ai_result.category,
        },
    )

    return {
        "id": str(observation.id),
        "inspection_id": data.inspection_id,
        "ai_analysis": {
            "category": ai_result.category,
            "severity": final_severity.value,
            "risk_score": ai_result.risk_score,
            "confidence": ai_result.confidence,
            "explanation": ai_result.explanation,
            "recommended_action": ai_result.recommended_action,
            "is_demo_fallback": ai_result.is_demo_fallback,
            "rule_adjusted": rule_result["adjusted"],
        },
        "violation_id": violation_id,
        "task_id": task_id,
    }


@router.get("/{observation_id}")
async def get_observation(
    observation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Observation).where(Observation.id == uuid.UUID(observation_id))
    )
    obs = result.scalar_one_or_none()
    if not obs:
        raise HTTPException(status_code=404, detail="Observation not found")

    return {
        "id": str(obs.id),
        "inspection_id": str(obs.inspection_id),
        "description": obs.description,
        "latitude": obs.latitude,
        "longitude": obs.longitude,
        "category": obs.category.value if obs.category else None,
        "photo_urls": obs.photo_urls,
        "captured_at": obs.captured_at.isoformat() if obs.captured_at else None,
        "created_at": obs.created_at.isoformat(),
    }


@router.post("/{observation_id}/photos")
async def upload_photo(
    observation_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload photo evidence for an observation."""
    result = await db.execute(
        select(Observation).where(Observation.id == uuid.UUID(observation_id))
    )
    obs = result.scalar_one_or_none()
    if not obs:
        raise HTTPException(status_code=404, detail="Observation not found")

    # Validate file type
    allowed_types = {"image/jpeg", "image/png", "image/webp"}
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Only JPEG, PNG, WebP images allowed")

    # Save file
    upload_dir = os.path.join(settings.UPLOAD_DIR, "observations", observation_id)
    os.makedirs(upload_dir, exist_ok=True)
    filename = f"{uuid.uuid4()}{os.path.splitext(file.filename)[1]}"
    file_path = os.path.join(upload_dir, filename)

    async with aiofiles.open(file_path, "wb") as f:
        content = await file.read()
        await f.write(content)

    # Update photo URLs
    photo_urls = obs.photo_urls or []
    photo_urls.append(f"/uploads/observations/{observation_id}/{filename}")
    obs.photo_urls = photo_urls

    return {"photo_url": f"/uploads/observations/{observation_id}/{filename}"}
