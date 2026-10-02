"""
AI Analysis Service — provider-agnostic LLM with deterministic fallback.

Pipeline:
  Input text → LLM → Structured JSON → Rule Engine → Final assessment

The LLM recommends. Rules validate. Humans verify.
NEVER fabricate legal/statutory references.
"""
import json
import logging
import random
from typing import Optional, Dict, Any
from datetime import datetime

import httpx
from pydantic import BaseModel

from app.config import settings

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# OUTPUT SCHEMA
# ─────────────────────────────────────────────

class AIAnalysisResult(BaseModel):
    category: str
    severity: str  # critical, high, medium, low
    risk_score: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    explanation: str
    recommended_action: str
    is_demo_fallback: bool = False
    model_used: str = "unknown"
    raw_response: Optional[Dict] = None


# ─────────────────────────────────────────────
# DEMO FALLBACK — deterministic, not random
# ─────────────────────────────────────────────

DEMO_SCENARIOS = {
    "ppe": {
        "category": "PPE",
        "severity": "high",
        "risk_score": 0.82,
        "confidence": 0.91,
        "explanation": (
            "Worker observed without mandatory Personal Protective Equipment (PPE) "
            "in an active work zone. Missing items include hard hat and safety harness. "
            "This directly violates DGMS Safety Circular requirements for underground operations."
        ),
        "recommended_action": (
            "1. Immediately halt work in affected zone. "
            "2. Issue PPE to all workers in zone. "
            "3. Conduct mandatory safety briefing. "
            "4. Document and report to Mine Safety Officer. "
            "5. Schedule PPE audit for entire section within 48 hours."
        ),
    },
    "fire": {
        "category": "Fire Safety",
        "severity": "critical",
        "risk_score": 0.94,
        "confidence": 0.96,
        "explanation": (
            "Fire safety equipment (extinguisher) found missing/expired in conveyor belt area. "
            "Combustible dust accumulation observed near electrical panels. "
            "Constitutes critical fire risk per CMR 2017 regulations."
        ),
        "recommended_action": (
            "1. Evacuate and isolate conveyor section immediately. "
            "2. Deploy emergency fire safety team. "
            "3. Replace/service all fire extinguishers. "
            "4. Clean dust accumulation from electrical panels. "
            "5. Report to statutory authority within 24 hours."
        ),
    },
    "electrical": {
        "category": "Electrical Safety",
        "severity": "high",
        "risk_score": 0.78,
        "confidence": 0.88,
        "explanation": (
            "Exposed electrical wiring observed in wet/damp area. "
            "Missing insulation cover on junction box. "
            "Risk of electric shock to workers and potential ignition source."
        ),
        "recommended_action": (
            "1. Isolate electrical circuit immediately. "
            "2. Install proper weatherproof insulation. "
            "3. Electrical safety audit of entire section. "
            "4. Update electrical maintenance schedule."
        ),
    },
    "ventilation": {
        "category": "Ventilation",
        "severity": "high",
        "risk_score": 0.76,
        "confidence": 0.85,
        "explanation": (
            "Ventilation fan observed as non-operational in underground section. "
            "Air quality readings below acceptable thresholds. "
            "Risk of toxic gas accumulation (CO, CH4)."
        ),
        "recommended_action": (
            "1. Evacuate underground section immediately. "
            "2. Repair/replace ventilation fan. "
            "3. Gas testing before re-entry. "
            "4. Report to Mine Safety Officer."
        ),
    },
    "environmental": {
        "category": "Environmental",
        "severity": "medium",
        "risk_score": 0.58,
        "confidence": 0.79,
        "explanation": (
            "Slurry discharge observed near drainage channel. "
            "Potential contamination of groundwater. "
            "Non-compliant with CPCB environmental clearance conditions."
        ),
        "recommended_action": (
            "1. Stop slurry discharge immediately. "
            "2. Contain and remediate affected area. "
            "3. Inspect and repair containment system. "
            "4. Report to State Pollution Control Board."
        ),
    },
}

KEYWORDS_TO_SCENARIO = {
    "ppe": "ppe", "helmet": "ppe", "harness": "ppe", "protective": "ppe",
    "fire": "fire", "extinguisher": "fire", "flammable": "fire", "smoke": "fire",
    "electrical": "electrical", "wiring": "electrical", "electric": "electrical",
    "ventilation": "ventilation", "air": "ventilation", "fan": "ventilation", "gas": "ventilation",
    "slurry": "environmental", "discharge": "environmental", "water": "environmental",
    "dust": "environmental", "environment": "environmental",
}


import re

def _get_demo_result(input_text: str) -> AIAnalysisResult:
    """Deterministic demo fallback based on input keywords with whole-word matching."""
    text_lower = input_text.lower()
    scenario_key = "ppe"  # default

    for keyword, scenario in KEYWORDS_TO_SCENARIO.items():
        if re.search(r'\b' + re.escape(keyword) + r'\b', text_lower):
            scenario_key = scenario
            break

    scenario = DEMO_SCENARIOS[scenario_key]
    return AIAnalysisResult(
        **scenario,
        is_demo_fallback=True,
        model_used="demo-fallback-v1",
    )


# ─────────────────────────────────────────────
# ANALYSIS PROMPT
# ─────────────────────────────────────────────

SYSTEM_PROMPT = """You are a coal mine safety compliance AI assistant.

Analyze the provided observation from a field inspection and return a structured JSON assessment.

IMPORTANT RULES:
1. Only reference real, well-known regulations (CMR 2017, DGMS guidelines, Mines Act 1952).
2. Do NOT fabricate regulation references.
3. If uncertain, lower confidence score.
4. The AI RECOMMENDS — human officers make final decisions.

Return ONLY valid JSON matching this schema:
{
  "category": "<PPE|Fire Safety|Electrical Safety|Ventilation|Environmental|Equipment|Labour/Worker Safety|Documentation|Emergency Preparedness>",
  "severity": "<critical|high|medium|low>",
  "risk_score": <float 0.0-1.0>,
  "confidence": <float 0.0-1.0>,
  "explanation": "<detailed explanation of the risk>",
  "recommended_action": "<numbered list of recommended corrective actions>"
}"""

USER_PROMPT_TEMPLATE = """Field Observation from Coal Mine Inspection:

Mine: {mine_name}
Zone: {zone_name}
Inspector Notes: {description}
Photos Captured: {photo_count}
GPS Location: {gps}

Analyze this observation for safety and compliance violations."""


# ─────────────────────────────────────────────
# AI SERVICE
# ─────────────────────────────────────────────

class AIService:
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.base_url = settings.OPENAI_BASE_URL
        self.model = settings.AI_MODEL

    async def analyze_observation(
        self,
        description: str,
        mine_name: str = "Unknown Mine",
        zone_name: str = "Unknown Zone",
        photo_count: int = 0,
        gps: str = "Not captured",
    ) -> AIAnalysisResult:
        """
        Analyze an observation using LLM.
        Falls back to deterministic demo mode if AI unavailable.
        """
        if not self.api_key:
            logger.info("AI_MODE: No API key — using demo fallback")
            return _get_demo_result(description)

        user_prompt = USER_PROMPT_TEMPLATE.format(
            mine_name=mine_name,
            zone_name=zone_name,
            description=description,
            photo_count=photo_count,
            gps=gps,
        )

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": user_prompt},
                        ],
                        "temperature": 0.1,
                        "response_format": {"type": "json_object"},
                    },
                )
                response.raise_for_status()
                data = response.json()
                raw_content = data["choices"][0]["message"]["content"]
                parsed = json.loads(raw_content)

                return AIAnalysisResult(
                    category=parsed.get("category", "PPE"),
                    severity=parsed.get("severity", "medium").lower(),
                    risk_score=float(parsed.get("risk_score", 0.5)),
                    confidence=float(parsed.get("confidence", 0.7)),
                    explanation=parsed.get("explanation", ""),
                    recommended_action=parsed.get("recommended_action", ""),
                    is_demo_fallback=False,
                    model_used=self.model,
                    raw_response=parsed,
                )
        except httpx.TimeoutException:
            logger.warning("AI request timed out — using demo fallback")
            return _get_demo_result(description)
        except Exception as e:
            logger.error(f"AI analysis failed: {e} — using demo fallback")
            return _get_demo_result(description)


ai_service = AIService()
analyze_observation = ai_service.analyze_observation

