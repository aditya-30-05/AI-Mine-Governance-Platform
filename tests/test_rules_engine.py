"""Unit tests for deterministic compliance rules engine."""
import pytest
from datetime import datetime, timedelta
from app.rules.engine import RuleEngine, ESCALATION_RULES, RECURRING_THRESHOLDS
from app.models import SeverityLevel, ViolationCategory, TaskPriority


@pytest.fixture
def engine():
    return RuleEngine()


def test_escalation_rules_critical_severity(engine):
    """Critical severity requires immediate escalation and critical task priority."""
    rule = ESCALATION_RULES[SeverityLevel.CRITICAL]
    assert rule["auto_escalate"] is True
    assert rule["escalate_within_hours"] == 0
    assert rule["task_priority"] == TaskPriority.CRITICAL


def test_escalation_rules_high_severity(engine):
    """High severity escalates within 24 hours."""
    rule = ESCALATION_RULES[SeverityLevel.HIGH]
    assert rule["auto_escalate"] is False
    assert rule["escalate_within_hours"] == 24
    assert rule["task_priority"] == TaskPriority.HIGH


def test_recurring_thresholds():
    """Verify recurring risk detection limits for critical categories."""
    assert RECURRING_THRESHOLDS[ViolationCategory.VENTILATION]["count"] == 2
    assert RECURRING_THRESHOLDS[ViolationCategory.FIRE_SAFETY]["count"] == 2
    assert RECURRING_THRESHOLDS[ViolationCategory.ELECTRICAL_SAFETY]["count"] == 2
    assert RECURRING_THRESHOLDS[ViolationCategory.PPE]["count"] == 3


def test_evaluate_severity_determination(engine):
    """Test rule engine severity evaluation logic and contextual escalation."""
    # Rule: Fire in extraction zone must be escalated to CRITICAL
    res_fire = engine.evaluate_severity(
        ai_severity="medium",
        category=ViolationCategory.FIRE_SAFETY,
        context={"zone_type": "extraction"},
    )
    assert res_fire["final_severity"] == SeverityLevel.CRITICAL.value
    assert res_fire["adjusted"] is True

    # Rule: PPE in underground mine escalated to at least MEDIUM
    res_ppe = engine.evaluate_severity(
        ai_severity="low",
        category=ViolationCategory.PPE,
        context={"mine_type": "underground"},
    )
    assert res_ppe["final_severity"] == SeverityLevel.MEDIUM.value
    assert res_ppe["adjusted"] is True


def test_task_priority_and_due_date(engine):
    """Verify task priority mapping and statutory due date logic."""
    crit_prio = engine.get_task_priority(SeverityLevel.CRITICAL)
    assert crit_prio == TaskPriority.CRITICAL

    now = datetime.utcnow()
    due_crit = engine.get_due_date(SeverityLevel.CRITICAL)
    assert due_crit > now

    due_high = engine.get_due_date(SeverityLevel.HIGH)
    assert due_high > due_crit


def test_check_recurring_logic(engine):
    """Test recurring risk detector."""
    # 3 PPE violations in 20 days should trigger recurring risk
    rec = engine.check_recurring(
        category=ViolationCategory.PPE.value,
        occurrence_count=3,
        days_window=20,
    )
    assert rec["is_recurring"] is True

    # 1 PPE violation in 10 days is not recurring
    non_rec = engine.check_recurring(
        category=ViolationCategory.PPE.value,
        occurrence_count=1,
        days_window=10,
    )
    assert non_rec["is_recurring"] is False
