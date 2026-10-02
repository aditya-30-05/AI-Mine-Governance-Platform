"""AI Analysis Router."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional

from app.auth.security import get_current_user
from app.models import User
from app.ai.analysis import ai_service

router = APIRouter(prefix="/ai", tags=["AI Analysis"])


class AnalyzeRequest(BaseModel):
    description: str
    mine_name: Optional[str] = "Unknown Mine"
    zone_name: Optional[str] = "Unknown Zone"
    photo_count: Optional[int] = 0
    gps: Optional[str] = "Not captured"


@router.post("/analyze-observation")
async def analyze_observation(
    data: AnalyzeRequest,
    current_user: User = Depends(get_current_user),
):
    """Standalone AI analysis endpoint for pre-submission preview."""
    result = await ai_service.analyze_observation(
        description=data.description,
        mine_name=data.mine_name,
        zone_name=data.zone_name,
        photo_count=data.photo_count,
        gps=data.gps,
    )
    return {
        "category": result.category,
        "severity": result.severity,
        "risk_score": result.risk_score,
        "confidence": result.confidence,
        "explanation": result.explanation,
        "recommended_action": result.recommended_action,
        "is_demo_fallback": result.is_demo_fallback,
        "model_used": result.model_used,
    }
