"""Unit tests for AI analysis service and fallback scenarios."""
import pytest
from app.ai.analysis import analyze_observation, AIAnalysisResult, DEMO_SCENARIOS


@pytest.mark.asyncio
async def test_ai_fallback_ppe_keyword():
    """Verify fallback detection correctly triggers for PPE keywords."""
    text = "Observed three workers without safety helmets and protective gear near face 2"
    result = await analyze_observation(description=text)

    assert isinstance(result, AIAnalysisResult)
    assert result.category == "PPE"
    assert result.severity in ["high", "critical", "medium"]
    assert 0.0 <= result.risk_score <= 1.0
    assert 0.0 <= result.confidence <= 1.0
    assert len(result.recommended_action) > 0


@pytest.mark.asyncio
async def test_ai_fallback_ventilation_keyword():
    """Verify ventilation scenario triggers high risk score."""
    text = "Methane gas build-up detected, auxiliary ventilation fan problem, airflow low"
    result = await analyze_observation(description=text)

    assert isinstance(result, AIAnalysisResult)
    assert result.category == "Ventilation"
    assert result.severity in ["high", "critical"]
    assert result.risk_score >= 0.70


@pytest.mark.asyncio
async def test_ai_fallback_fire_safety():
    """Verify fire safety scenario triggers critical severity."""
    text = "Smoke and fire hazard detected near conveyor belt, missing fire extinguisher"
    result = await analyze_observation(description=text)

    assert isinstance(result, AIAnalysisResult)
    assert result.category == "Fire Safety"
    assert result.severity == "critical"
    assert result.risk_score >= 0.90


@pytest.mark.asyncio
async def test_ai_fallback_electrical_hazard():
    """Verify electrical safety detection."""
    text = "Exposed electrical wiring without insulation in wet shaft area"
    result = await analyze_observation(description=text)

    assert isinstance(result, AIAnalysisResult)
    assert result.category == "Electrical Safety"
    assert result.severity in ["high", "critical"]


def test_demo_scenarios_data_integrity():
    """Verify all predefined demo scenarios have valid structured outputs."""
    for key, scenario in DEMO_SCENARIOS.items():
        assert "category" in scenario
        assert "severity" in scenario
        assert "risk_score" in scenario
        assert 0.0 <= scenario["risk_score"] <= 1.0
        assert "recommended_action" in scenario
