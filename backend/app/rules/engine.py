"""
Rule Engine — deterministic compliance rules.
AI recommends, rules validate, humans verify.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from app.models import SeverityLevel, ViolationCategory, TaskPriority


# ─────────────────────────────────────────────
# RULE DEFINITIONS
# ─────────────────────────────────────────────

ESCALATION_RULES = {
    SeverityLevel.CRITICAL: {
        "auto_escalate": True,
        "escalate_within_hours": 0,  # Immediate
        "task_priority": TaskPriority.CRITICAL,
        "description": "Critical violation requires immediate escalation",
    },
    SeverityLevel.HIGH: {
        "auto_escalate": False,
        "escalate_within_hours": 24,
        "task_priority": TaskPriority.HIGH,
        "description": "High severity requires high-priority task",
    },
    SeverityLevel.MEDIUM: {
        "auto_escalate": False,
        "escalate_within_hours": 72,
        "task_priority": TaskPriority.MEDIUM,
        "description": "Medium severity requires standard follow-up",
    },
    SeverityLevel.LOW: {
        "auto_escalate": False,
        "escalate_within_hours": 168,  # 7 days
        "task_priority": TaskPriority.LOW,
        "description": "Low severity requires monitoring",
    },
}

RECURRING_THRESHOLDS = {
    "default": {"count": 3, "days": 30},
    ViolationCategory.PPE: {"count": 3, "days": 30},
    ViolationCategory.FIRE_SAFETY: {"count": 2, "days": 30},
    ViolationCategory.ELECTRICAL_SAFETY: {"count": 2, "days": 30},
    ViolationCategory.VENTILATION: {"count": 2, "days": 30},
}

DOCUMENT_EXPIRY_WARNING_DAYS = 30  # warn if expiring within 30 days


# ─────────────────────────────────────────────
# RULE ENGINE
# ─────────────────────────────────────────────

class RuleEngine:
    """Deterministic rule engine for compliance validation."""

    def evaluate_severity(
        self,
        ai_severity: str,
        category: str,
        context: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Validate and potentially adjust AI-recommended severity.
        Rules can escalate severity but typically don't reduce it.
        """
        severity = SeverityLevel(ai_severity.lower()) if ai_severity else SeverityLevel.MEDIUM
        adjustments = []

        context = context or {}

        # Rule: PPE + underground = escalate to HIGH minimum
        if category == ViolationCategory.PPE and context.get("mine_type") == "underground":
            if severity == SeverityLevel.LOW:
                severity = SeverityLevel.MEDIUM
                adjustments.append("Escalated: PPE violation in underground mine")

        # Rule: Fire in extraction zone = CRITICAL minimum
        if category == ViolationCategory.FIRE_SAFETY and context.get("zone_type") == "extraction":
            severity = SeverityLevel.CRITICAL
            adjustments.append("Escalated: Fire safety in extraction zone is always CRITICAL")

        # Rule: Multiple photos of same issue = +1 severity step
        photo_count = context.get("photo_count", 0)
        if photo_count >= 3 and severity == SeverityLevel.LOW:
            severity = SeverityLevel.MEDIUM
            adjustments.append("Escalated: Multiple evidence photos indicate confirmed violation")

        return {
            "final_severity": severity.value,
            "adjusted": len(adjustments) > 0,
            "adjustments": adjustments,
        }

    def should_create_task(self, severity: SeverityLevel) -> bool:
        return severity in [SeverityLevel.CRITICAL, SeverityLevel.HIGH, SeverityLevel.MEDIUM]

    def get_task_priority(self, severity: SeverityLevel) -> TaskPriority:
        return ESCALATION_RULES.get(severity, ESCALATION_RULES[SeverityLevel.MEDIUM])["task_priority"]

    def get_due_date(self, severity: SeverityLevel) -> datetime:
        hours = ESCALATION_RULES.get(severity, ESCALATION_RULES[SeverityLevel.MEDIUM])["escalate_within_hours"]
        if hours == 0:
            hours = 4  # Critical: 4-hour initial response
        return datetime.utcnow() + timedelta(hours=hours)

    def should_auto_escalate(self, severity: SeverityLevel) -> bool:
        return ESCALATION_RULES.get(severity, {}).get("auto_escalate", False)

    def check_recurring(
        self,
        category: str,
        occurrence_count: int,
        days_window: int,
    ) -> Dict[str, Any]:
        """Check if violation pattern meets recurring risk threshold."""
        try:
            cat = ViolationCategory(category)
        except ValueError:
            cat = None

        threshold = RECURRING_THRESHOLDS.get(cat, RECURRING_THRESHOLDS["default"])

        is_recurring = (
            occurrence_count >= threshold["count"]
            and days_window <= threshold["days"]
        )

        return {
            "is_recurring": is_recurring,
            "threshold_count": threshold["count"],
            "threshold_days": threshold["days"],
            "occurrence_count": occurrence_count,
            "message": (
                f"RECURRING RISK: {occurrence_count} violations in {days_window} days "
                f"(threshold: {threshold['count']} in {threshold['days']} days)"
                if is_recurring
                else "Not yet recurring"
            ),
        }

    def check_document_compliance(
        self,
        issue_date: Optional[datetime],
        expiry_date: Optional[datetime],
    ) -> Dict[str, Any]:
        """Check document compliance status based on dates."""
        now = datetime.utcnow()

        if expiry_date is None:
            return {"status": "pending_review", "message": "No expiry date set"}

        if expiry_date < now:
            return {
                "status": "expired",
                "severity": "critical",
                "message": f"Document expired on {expiry_date.date()}",
            }

        days_to_expiry = (expiry_date - now).days
        if days_to_expiry <= DOCUMENT_EXPIRY_WARNING_DAYS:
            return {
                "status": "warning",
                "severity": "high",
                "days_to_expiry": days_to_expiry,
                "message": f"Document expires in {days_to_expiry} days",
            }

        return {
            "status": "compliant",
            "severity": "low",
            "days_to_expiry": days_to_expiry,
            "message": "Document is valid",
        }


rule_engine = RuleEngine()
