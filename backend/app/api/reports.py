"""Reports API."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid

from app.database import get_db
from app.auth.security import get_current_user
from app.models import ReportJob, User

router = APIRouter(prefix="/reports", tags=["Reports"])


class ReportRequest(BaseModel):
    mine_id: Optional[str] = None
    report_type: str = "compliance"  # compliance, incident, trend
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    format: str = "pdf"  # pdf, excel, csv


@router.post("/generate", status_code=202)
async def generate_report(
    data: ReportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Queue a report generation job."""
    job = ReportJob(
        mine_id=uuid.UUID(data.mine_id) if data.mine_id else None,
        requested_by_id=current_user.id,
        report_type=data.report_type,
        parameters={
            "date_from": data.date_from.isoformat() if data.date_from else None,
            "date_to": data.date_to.isoformat() if data.date_to else None,
            "format": data.format,
        },
        status="pending",
    )
    db.add(job)
    await db.flush()

    # In production: dispatch to Celery worker
    # For demo: generate synchronously
    try:
        from app.services.report_service import generate_report_sync
        file_path = await generate_report_sync(str(job.id), data, db)
        job.status = "complete"
        job.file_path = file_path
        job.completed_at = datetime.utcnow()
    except Exception as e:
        job.status = "failed"
        job.error_message = str(e)

    return {
        "job_id": str(job.id),
        "status": job.status,
        "file_path": job.file_path,
    }


@router.get("/{job_id}")
async def get_report_status(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ReportJob).where(ReportJob.id == uuid.UUID(job_id))
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Report job not found")

    return {
        "job_id": str(job.id),
        "status": job.status,
        "report_type": job.report_type,
        "file_path": job.file_path,
        "error_message": job.error_message,
        "created_at": job.created_at.isoformat(),
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
    }
