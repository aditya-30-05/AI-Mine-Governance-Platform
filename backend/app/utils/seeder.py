"""
Comprehensive seed data for SIH demo.
Creates Mine A storyline: PPE violations → recurring → task → overdue → escalation → resolution → verification.
Dashboard target: Compliance 87%, Critical 3, High 8, Medium 14, Overdue 4, Recurring 3, Pending 7.
SYNTHETIC DATA — NOT real Coal India data.
"""
import uuid
import random
import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models import (
    Subsidiary, Mine, MineZone, User, Inspection, Observation,
    AIAnalysis, Violation, RecurringRisk, Task, TaskHistory,
    ComplianceDocument, Notification, AuditLog,
    UserRole, InspectionStatus, SeverityLevel, ViolationCategory,
    TaskStatus, TaskPriority, ComplianceStatus, SyncStatus, NotificationType
)
from app.auth.security import hash_password
from app.audit.service import log_audit

logger = logging.getLogger(__name__)

_SEEDED = False  # Global flag to prevent re-seeding


def _ref(prefix: str) -> str:
    ts = datetime.utcnow().strftime("%Y%m%d")
    uid = str(uuid.uuid4())[:6].upper()
    return f"{prefix}-{ts}-{uid}"


def _dt(days_ago: float = 0, hours_ago: float = 0) -> datetime:
    return datetime.utcnow() - timedelta(days=days_ago, hours=hours_ago)


async def run_seed():
    global _SEEDED
    if _SEEDED:
        return
    _SEEDED = True

    async with AsyncSessionLocal() as db:
        # Check if already seeded
        existing = await db.execute(select(func.count(User.id)))
        count = existing.scalar_one()
        if count > 0:
            logger.info("Database already seeded, skipping.")
            return

        logger.info("Seeding database with SIH demo data...")
        await _seed_all(db)
        await db.commit()
        logger.info("Seeding complete.")


async def _seed_all(db: AsyncSession):
    # ── SUBSIDIARIES ──
    sub1 = Subsidiary(name="Eastern Coalfields Limited", code="ECL", state="West Bengal", region="East")
    sub2 = Subsidiary(name="Bharat Coking Coal Limited", code="BCCL", state="Jharkhand", region="East")
    sub3 = Subsidiary(name="Central Coalfields Limited", code="CCL", state="Jharkhand", region="Central")
    db.add_all([sub1, sub2, sub3])
    await db.flush()

    # ── MINES (10) — Mine A is the primary demo mine ──
    mine_a = Mine(
        name="Mine A — Ramgarh Colliery",
        code="MINE-A",
        subsidiary_id=sub1.id,
        location_name="Ramgarh, Jharkhand",
        state="Jharkhand",
        district="Ramgarh",
        latitude=23.6250,
        longitude=85.5140,
        mine_type="underground",
        capacity_mtpa=2.5,
        is_active=True,
    )
    other_mines = [
        Mine(name=f"Mine {chr(65+i)} — Demo Colliery {i}", code=f"MINE-{chr(65+i)}",
             subsidiary_id=random.choice([sub1.id, sub2.id, sub3.id]),
             latitude=23.5 + i * 0.1, longitude=85.4 + i * 0.15,
             mine_type=random.choice(["underground", "opencast"]),
             capacity_mtpa=random.uniform(1.0, 5.0), is_active=True)
        for i in range(1, 10)
    ]
    db.add(mine_a)
    db.add_all(other_mines)
    await db.flush()

    # ── MINE ZONES ──
    zones = [
        MineZone(mine_id=mine_a.id, name="Extraction Zone 1", zone_type="extraction"),
        MineZone(mine_id=mine_a.id, name="Transport Corridor A", zone_type="transport"),
        MineZone(mine_id=mine_a.id, name="Processing Plant", zone_type="processing"),
        MineZone(mine_id=mine_a.id, name="Entry Gate", zone_type="entry"),
        MineZone(mine_id=mine_a.id, name="Electrical Substation", zone_type="electrical"),
    ]
    db.add_all(zones)
    await db.flush()
    zone_extraction = zones[0]
    zone_transport = zones[1]

    # ── USERS (30) ──
    # Core demo users
    admin = User(
        employee_id="EMP-ADMIN-001",
        email="admin@coalmine.gov.in",
        full_name="System Administrator",
        hashed_password=hash_password("Admin@1234"),
        role=UserRole.ADMIN,
        department="IT Administration",
        subsidiary_id=sub1.id,
        is_active=True,
    )
    manager_a = User(
        employee_id="EMP-MGR-001",
        email="manager.a@coalmine.gov.in",
        full_name="Rajesh Kumar Singh",
        hashed_password=hash_password("Manager@1234"),
        role=UserRole.MINE_MANAGER,
        department="Mine Operations",
        subsidiary_id=sub1.id,
        mine_id=mine_a.id,
        is_active=True,
        phone="+91-9876543210",
    )
    compliance_officer = User(
        employee_id="EMP-CO-001",
        email="compliance@coalmine.gov.in",
        full_name="Priya Sharma",
        hashed_password=hash_password("Compliance@1234"),
        role=UserRole.COMPLIANCE_OFFICER,
        department="Safety & Compliance",
        subsidiary_id=sub1.id,
        mine_id=mine_a.id,
        is_active=True,
    )
    field_officer = User(
        employee_id="EMP-FO-001",
        email="field.officer@coalmine.gov.in",
        full_name="Amit Mahato",
        hashed_password=hash_password("Field@1234"),
        role=UserRole.FIELD_OFFICER,
        department="Field Operations",
        subsidiary_id=sub1.id,
        mine_id=mine_a.id,
        is_active=True,
        phone="+91-9812345678",
    )
    field_officer2 = User(
        employee_id="EMP-FO-002",
        email="field.officer2@coalmine.gov.in",
        full_name="Suresh Yadav",
        hashed_password=hash_password("Field@1234"),
        role=UserRole.FIELD_OFFICER,
        department="Field Operations",
        subsidiary_id=sub1.id,
        mine_id=mine_a.id,
        is_active=True,
    )
    corporate_mgr = User(
        employee_id="EMP-CORP-001",
        email="corporate@coalmine.gov.in",
        full_name="Dr. Meera Pillai",
        hashed_password=hash_password("Corporate@1234"),
        role=UserRole.CORPORATE_MANAGER,
        department="Corporate Safety",
        subsidiary_id=sub1.id,
        is_active=True,
    )

    # Extra users for realism
    extra_users = [
        User(
            employee_id=f"EMP-{i:03d}",
            email=f"user{i}@coalmine.gov.in",
            full_name=random.choice([
                "Vikram Gupta", "Sanjay Tiwari", "Ramesh Mishra", "Deepak Pandey",
                "Anjali Singh", "Nisha Kumari", "Rohit Verma", "Kavita Rao",
                "Mohan Das", "Lakshmi Naidu", "Ganesh Patel", "Sunita Jha",
                "Arun Kumar", "Pooja Mishra", "Dinesh Shah", "Rekha Devi",
                "Sunil Yadav", "Kaveri Das", "Ravi Kumar", "Meena Sharma",
                "Prakash Singh", "Usha Pandey", "Dilip Kumar", "Anita Roy",
            ]),
            hashed_password=hash_password("User@1234"),
            role=random.choice([UserRole.FIELD_OFFICER, UserRole.COMPLIANCE_OFFICER]),
            mine_id=random.choice([mine_a.id] + [m.id for m in other_mines[:5]]),
            subsidiary_id=random.choice([sub1.id, sub2.id, sub3.id]),
            is_active=True,
        )
        for i in range(7, 31)
    ]

    db.add_all([admin, manager_a, compliance_officer, field_officer, field_officer2, corporate_mgr])
    db.add_all(extra_users)
    await db.flush()

    # Set mine manager
    mine_a.manager_id = manager_a.id

    # ── COMPLIANCE RULES ──
    rules_data = [
        ("RULE-PPE-001", "Hard Hat Mandatory", ViolationCategory.PPE, SeverityLevel.HIGH, "CMR 2017, Reg. 32"),
        ("RULE-PPE-002", "Safety Harness Required", ViolationCategory.PPE, SeverityLevel.HIGH, "CMR 2017, Reg. 33"),
        ("RULE-FIRE-001", "Fire Extinguisher Operational", ViolationCategory.FIRE_SAFETY, SeverityLevel.CRITICAL, "CMR 2017, Reg. 67"),
        ("RULE-ELEC-001", "No Exposed Wiring", ViolationCategory.ELECTRICAL_SAFETY, SeverityLevel.HIGH, "CMR 2017, Reg. 78"),
        ("RULE-VENT-001", "Ventilation Operational", ViolationCategory.VENTILATION, SeverityLevel.HIGH, "CMR 2017, Reg. 45"),
        ("RULE-ENV-001", "No Unauthorized Discharge", ViolationCategory.ENVIRONMENTAL, SeverityLevel.MEDIUM, "CPCB Guidelines"),
        ("RULE-EQUIP-001", "Equipment Certification Valid", ViolationCategory.EQUIPMENT, SeverityLevel.MEDIUM, "CMR 2017, Reg. 89"),
        ("RULE-DOC-001", "License Current", ViolationCategory.DOCUMENTATION, SeverityLevel.CRITICAL, "Mines Act 1952, Sec. 5"),
    ]
    from app.models import ComplianceRule
    for code, name, cat, sev, ref in rules_data:
        rule = ComplianceRule(
            code=code, name=name, category=cat,
            severity_if_violated=sev, regulation_reference=ref,
            auto_escalate=(sev == SeverityLevel.CRITICAL),
            recurring_threshold_count=3, recurring_threshold_days=30,
            is_active=True,
        )
        db.add(rule)
    await db.flush()

    # ════════════════════════════════════════════════
    # MINE A STORYLINE — The core SIH demo narrative
    # ════════════════════════════════════════════════

    # --- INSPECTION 1: 35 days ago (first PPE violation) ---
    insp1 = Inspection(
        reference_number=_ref("INS"),
        mine_id=mine_a.id,
        inspector_id=field_officer.id,
        inspection_type="routine",
        status=InspectionStatus.COMPLETED,
        started_at=_dt(35, 8),
        completed_at=_dt(35, 10),
        shift="morning",
        start_latitude=23.6250, start_longitude=85.5140,
        notes="Routine morning inspection. Zone 1 access.",
        overall_compliance_score=0.82,
        sync_status=SyncStatus.SYNCED,
    )
    db.add(insp1)
    await db.flush()

    obs1 = Observation(
        inspection_id=insp1.id,
        zone_id=zone_extraction.id,
        description="Worker in extraction zone not wearing mandatory hard hat. "
                    "Approximately 5 workers observed without PPE near coal face. "
                    "Area supervisor not present.",
        latitude=23.6258, longitude=85.5148,
        photo_urls=["/demo/photos/ppe_violation_1.jpg"],
        captured_at=_dt(35, 8.5),
    )
    db.add(obs1)
    await db.flush()

    ai1 = AIAnalysis(
        input_text=obs1.description,
        model_used="demo-fallback-v1",
        is_demo_fallback=True,
        category="PPE",
        severity=SeverityLevel.HIGH,
        risk_score=0.82,
        confidence=0.91,
        explanation="Multiple workers without PPE in active extraction zone. "
                    "Direct violation of DGMS safety requirements. High injury risk.",
        recommended_action="1. Halt operations 2. Issue PPE immediately 3. Safety briefing 4. Document",
        rule_adjusted=False,
    )
    db.add(ai1)
    await db.flush()

    obs1.ai_analysis_id = ai1.id
    obs1.category = ViolationCategory.PPE

    vio1 = Violation(
        reference_number=_ref("VIO"),
        mine_id=mine_a.id,
        inspection_id=insp1.id,
        observation_id=obs1.id,
        category=ViolationCategory.PPE,
        severity=SeverityLevel.HIGH,
        description=obs1.description,
        latitude=23.6258, longitude=85.5148,
        zone_id=zone_extraction.id,
        compliance_status=ComplianceStatus.NON_COMPLIANT,
        is_recurring=False,
        photo_urls=["/demo/photos/ppe_violation_1.jpg"],
    )
    db.add(vio1)
    await db.flush()

    task1 = Task(
        reference_number=_ref("TSK"),
        mine_id=mine_a.id,
        violation_id=vio1.id,
        title="[HIGH] PPE Violation — Mine A Extraction Zone 1",
        description="5 workers observed without hard hats. Immediate corrective action required.",
        category=ViolationCategory.PPE,
        priority=TaskPriority.HIGH,
        status=TaskStatus.VERIFIED,  # Resolved in past
        assignee_id=field_officer2.id,
        assigned_by_id=manager_a.id,
        due_date=_dt(28),
        started_at=_dt(34),
        resolved_at=_dt(30),
        verified_at=_dt(29),
        resolution_note="PPE issued to all workers. Mandatory briefing completed. "
                        "Area supervisor assigned to monitor compliance.",
        verification_note="Verified on-site. All workers wearing PPE. Supervisor present.",
        escalation_count=0,
    )
    db.add(task1)
    await db.flush()

    # Task history for task1
    for action, old_s, new_s, days_ago, note in [
        ("created", None, TaskStatus.OPEN, 35, "Task created from violation"),
        ("assigned", TaskStatus.OPEN, TaskStatus.ASSIGNED, 34.5, "Assigned by mine manager"),
        ("started", TaskStatus.ASSIGNED, TaskStatus.IN_PROGRESS, 34, "Work started"),
        ("resolved", TaskStatus.IN_PROGRESS, TaskStatus.RESOLVED, 30, "All PPE distributed"),
        ("verified", TaskStatus.RESOLVED, TaskStatus.VERIFIED, 29, "On-site verification passed"),
    ]:
        h = TaskHistory(
            task_id=task1.id,
            changed_by_id=manager_a.id if "assign" in action or "verify" in action else field_officer2.id,
            action=action,
            old_status=old_s,
            new_status=new_s,
            note=note,
        )
        h.created_at = _dt(days_ago)
        db.add(h)
    await db.flush()

    # --- INSPECTION 2: 20 days ago (second PPE violation — same zone) ---
    insp2 = Inspection(
        reference_number=_ref("INS"),
        mine_id=mine_a.id,
        inspector_id=field_officer.id,
        inspection_type="routine",
        status=InspectionStatus.COMPLETED,
        started_at=_dt(20, 7),
        completed_at=_dt(20, 9),
        shift="morning",
        start_latitude=23.6251, start_longitude=85.5142,
        overall_compliance_score=0.79,
        sync_status=SyncStatus.SYNCED,
    )
    db.add(insp2)
    await db.flush()

    obs2 = Observation(
        inspection_id=insp2.id,
        zone_id=zone_extraction.id,
        description="Again observed workers without safety harness and hard hat in Extraction Zone 1. "
                    "Different shift workers. PPE storage reported as depleted by workers. "
                    "This is the second occurrence in the same zone within 20 days.",
        latitude=23.6260, longitude=85.5150,
        photo_urls=["/demo/photos/ppe_violation_2a.jpg", "/demo/photos/ppe_violation_2b.jpg"],
        captured_at=_dt(20, 7.5),
    )
    db.add(obs2)
    await db.flush()

    ai2 = AIAnalysis(
        input_text=obs2.description,
        model_used="demo-fallback-v1",
        is_demo_fallback=True,
        category="PPE",
        severity=SeverityLevel.HIGH,
        risk_score=0.85,
        confidence=0.93,
        explanation="Second PPE violation in same extraction zone. Recurring pattern indicates "
                    "systemic failure in PPE compliance. Requires investigation of root cause.",
        recommended_action="1. Emergency PPE audit 2. Investigate supply chain 3. "
                           "Mandatory retraining for all shift workers 4. Daily PPE checks by supervisor",
        rule_adjusted=False,
    )
    db.add(ai2)
    await db.flush()

    obs2.ai_analysis_id = ai2.id
    obs2.category = ViolationCategory.PPE

    vio2 = Violation(
        reference_number=_ref("VIO"),
        mine_id=mine_a.id,
        inspection_id=insp2.id,
        observation_id=obs2.id,
        category=ViolationCategory.PPE,
        severity=SeverityLevel.HIGH,
        description=obs2.description,
        latitude=23.6260, longitude=85.5150,
        zone_id=zone_extraction.id,
        compliance_status=ComplianceStatus.NON_COMPLIANT,
        is_recurring=False,
        photo_urls=["/demo/photos/ppe_violation_2a.jpg", "/demo/photos/ppe_violation_2b.jpg"],
    )
    db.add(vio2)
    await db.flush()

    task2 = Task(
        reference_number=_ref("TSK"),
        mine_id=mine_a.id,
        violation_id=vio2.id,
        title="[HIGH] PPE Repeat Violation — Mine A Extraction Zone 1",
        description="Second PPE violation in 20 days. Investigate systemic failure.",
        category=ViolationCategory.PPE,
        priority=TaskPriority.HIGH,
        status=TaskStatus.IN_PROGRESS,
        assignee_id=field_officer2.id,
        assigned_by_id=manager_a.id,
        due_date=_dt(13),  # Was due 13 days ago → OVERDUE
        started_at=_dt(19),
        escalation_count=0,
    )
    db.add(task2)
    await db.flush()

    # --- INSPECTION 3: 10 days ago (THIRD PPE — triggers RECURRING RISK) ---
    insp3 = Inspection(
        reference_number=_ref("INS"),
        mine_id=mine_a.id,
        inspector_id=field_officer.id,
        inspection_type="special",
        status=InspectionStatus.COMPLETED,
        started_at=_dt(10, 6),
        completed_at=_dt(10, 8),
        shift="morning",
        start_latitude=23.6252, start_longitude=85.5143,
        notes="Special inspection following second PPE violation.",
        overall_compliance_score=0.75,
        sync_status=SyncStatus.SYNCED,
    )
    db.add(insp3)
    await db.flush()

    obs3 = Observation(
        inspection_id=insp3.id,
        zone_id=zone_extraction.id,
        description="THIRD PPE violation in Extraction Zone 1 within 30 days. "
                    "Workers bypassing PPE check at zone entry. No supervisor present. "
                    "PPE board shows expired dates. Multiple workers — approx 8 — without helmets.",
        latitude=23.6262, longitude=85.5152,
        photo_urls=["/demo/photos/ppe_violation_3a.jpg", "/demo/photos/ppe_violation_3b.jpg",
                    "/demo/photos/ppe_violation_3c.jpg"],
        captured_at=_dt(10, 6.5),
    )
    db.add(obs3)
    await db.flush()

    ai3 = AIAnalysis(
        input_text=obs3.description,
        model_used="demo-fallback-v1",
        is_demo_fallback=True,
        category="PPE",
        severity=SeverityLevel.HIGH,
        risk_score=0.89,
        confidence=0.95,
        explanation="Third PPE violation in extraction zone within 30 days. "
                    "This constitutes a RECURRING COMPLIANCE RISK requiring systemic intervention. "
                    "Risk of serious worker injury is high.",
        recommended_action="RECURRING RISK ACTION PLAN: 1. Escalate to Corporate Safety Officer "
                           "2. Mandatory zone shutdown until compliance confirmed "
                           "3. Full PPE audit and replacement 4. Daily supervisor sign-off required "
                           "5. Root cause analysis report within 72 hours",
        rule_adjusted=True,
        rule_adjustment_reason="Escalated: Third occurrence triggers RECURRING RISK protocol",
    )
    db.add(ai3)
    await db.flush()

    obs3.ai_analysis_id = ai3.id
    obs3.category = ViolationCategory.PPE

    # Create Recurring Risk
    ppe_recurring = RecurringRisk(
        mine_id=mine_a.id,
        zone_id=zone_extraction.id,
        category=ViolationCategory.PPE,
        occurrence_count=4,  # 4 in 30 days
        first_occurrence=_dt(35),
        last_occurrence=_dt(10),
        time_window_days=30,
        severity=SeverityLevel.HIGH,
        status="active",
        recommended_action=(
            "RECURRING PPE RISK: 4 violations in 30 days in Extraction Zone 1. "
            "Systemic corrective action required: zone shutdown, PPE audit, supervisor training, "
            "daily compliance checks, root cause analysis."
        ),
        trend="increasing",
    )
    db.add(ppe_recurring)
    await db.flush()

    vio3 = Violation(
        reference_number=_ref("VIO"),
        mine_id=mine_a.id,
        inspection_id=insp3.id,
        observation_id=obs3.id,
        category=ViolationCategory.PPE,
        severity=SeverityLevel.HIGH,
        description=obs3.description,
        latitude=23.6262, longitude=85.5152,
        zone_id=zone_extraction.id,
        compliance_status=ComplianceStatus.NON_COMPLIANT,
        is_recurring=True,
        recurring_risk_id=ppe_recurring.id,
        photo_urls=obs3.photo_urls,
    )
    db.add(vio3)
    await db.flush()

    # Update earlier violations as part of recurring pattern
    vio1.is_recurring = True
    vio1.recurring_risk_id = ppe_recurring.id
    vio2.is_recurring = True
    vio2.recurring_risk_id = ppe_recurring.id

    # Escalated task for recurring
    task3 = Task(
        reference_number=_ref("TSK"),
        mine_id=mine_a.id,
        violation_id=vio3.id,
        recurring_risk_id=ppe_recurring.id,
        title="[HIGH] RECURRING PPE RISK — Immediate Systemic Action Required",
        description=ai3.recommended_action,
        category=ViolationCategory.PPE,
        priority=TaskPriority.HIGH,
        status=TaskStatus.ESCALATED,
        assignee_id=manager_a.id,
        assigned_by_id=manager_a.id,
        escalated_to_id=compliance_officer.id,
        due_date=_dt(3),  # OVERDUE
        started_at=_dt(9),
        escalation_count=1,
        escalation_note="Recurring PPE violations (4 in 30 days). Escalated to Compliance Officer for systemic review.",
        reminder_date=_dt(7),
    )
    db.add(task3)
    await db.flush()

    # --- CRITICAL VIOLATIONS (3 for dashboard) ---
    # Fire Safety — CRITICAL
    insp4 = Inspection(
        reference_number=_ref("INS"),
        mine_id=mine_a.id,
        inspector_id=field_officer.id,
        inspection_type="special",
        status=InspectionStatus.COMPLETED,
        started_at=_dt(5, 8),
        completed_at=_dt(5, 10),
        shift="morning",
        start_latitude=23.6255, start_longitude=85.5145,
        overall_compliance_score=0.65,
        sync_status=SyncStatus.SYNCED,
    )
    db.add(insp4)
    await db.flush()

    critical_descriptions = [
        ("Fire extinguisher missing from conveyor belt corridor. Heavy coal dust accumulation "
         "near electrical panels. Multiple ignition sources present. IMMEDIATE DANGER.",
         ViolationCategory.FIRE_SAFETY, SeverityLevel.CRITICAL, zone_extraction.id),
        ("Emergency escape route blocked by coal stockpile. Workers unable to evacuate safely. "
         "Padlocked emergency door — lock rusted shut.",
         ViolationCategory.EMERGENCY_PREPAREDNESS, SeverityLevel.CRITICAL, zone_transport.id),
        ("Electrical panel cover missing, live wires exposed in wet underground section. "
         "Risk of electrocution and ignition in methane-present area.",
         ViolationCategory.ELECTRICAL_SAFETY, SeverityLevel.CRITICAL, zone_extraction.id),
    ]

    for desc, cat, sev, zone_id in critical_descriptions:
        obs_c = Observation(
            inspection_id=insp4.id,
            zone_id=zone_id,
            description=desc,
            latitude=23.6253 + random.uniform(-0.001, 0.001),
            longitude=85.5143 + random.uniform(-0.001, 0.001),
            captured_at=_dt(5, random.uniform(8, 10)),
        )
        db.add(obs_c)
        await db.flush()

        ai_c = AIAnalysis(
            input_text=desc,
            model_used="demo-fallback-v1",
            is_demo_fallback=True,
            category=cat.value,
            severity=sev,
            risk_score=0.94,
            confidence=0.96,
            explanation=f"Critical {cat.value} violation detected. Immediate risk to worker safety.",
            recommended_action="Immediate evacuation and isolation of affected area. Emergency response required.",
        )
        db.add(ai_c)
        await db.flush()

        obs_c.ai_analysis_id = ai_c.id
        obs_c.category = cat

        vio_c = Violation(
            reference_number=_ref("VIO"),
            mine_id=mine_a.id,
            inspection_id=insp4.id,
            observation_id=obs_c.id,
            category=cat,
            severity=sev,
            description=desc,
            latitude=obs_c.latitude,
            longitude=obs_c.longitude,
            zone_id=zone_id,
            compliance_status=ComplianceStatus.NON_COMPLIANT,
        )
        db.add(vio_c)
        await db.flush()

        task_c = Task(
            reference_number=_ref("TSK"),
            mine_id=mine_a.id,
            violation_id=vio_c.id,
            title=f"[CRITICAL] {cat.value} — IMMEDIATE ACTION REQUIRED",
            description=ai_c.recommended_action,
            category=cat,
            priority=TaskPriority.CRITICAL,
            status=TaskStatus.ESCALATED,
            assignee_id=manager_a.id,
            assigned_by_id=manager_a.id,
            escalated_to_id=compliance_officer.id,
            due_date=_dt(4),  # OVERDUE (was 4 days ago)
            escalation_count=1,
        )
        db.add(task_c)
        await db.flush()

    # ── Additional HIGH violations (to reach target: 8 high) ──
    high_violation_data = [
        ("Ventilation fan #3 in Block B not operational. Air quality degraded.",
         ViolationCategory.VENTILATION, SeverityLevel.HIGH, 15),
        ("Inadequate roof support in gallery 4. Loose rock visible.",
         ViolationCategory.EQUIPMENT, SeverityLevel.HIGH, 12),
        ("Oil spill near machinery depot — approximately 50 liters.",
         ViolationCategory.ENVIRONMENTAL, SeverityLevel.HIGH, 18),
        ("First aid kit empty in transport zone. Missing medicines.",
         ViolationCategory.EMERGENCY_PREPAREDNESS, SeverityLevel.HIGH, 22),
        ("Worker shift duration exceeded 10 hours without authorized break.",
         ViolationCategory.LABOUR_WORKER_SAFETY, SeverityLevel.HIGH, 8),
    ]

    for desc, cat, sev, days_ago_insp in high_violation_data:
        v_insp = Inspection(
            reference_number=_ref("INS"),
            mine_id=mine_a.id,
            inspector_id=field_officer.id,
            inspection_type="routine",
            status=InspectionStatus.COMPLETED,
            started_at=_dt(days_ago_insp),
            overall_compliance_score=0.80,
            sync_status=SyncStatus.SYNCED,
        )
        db.add(v_insp)
        await db.flush()

        v_obs = Observation(
            inspection_id=v_insp.id,
            description=desc,
            latitude=23.6250 + random.uniform(-0.01, 0.01),
            longitude=85.5140 + random.uniform(-0.01, 0.01),
        )
        db.add(v_obs)
        await db.flush()

        v_vio = Violation(
            reference_number=_ref("VIO"),
            mine_id=mine_a.id,
            inspection_id=v_insp.id,
            observation_id=v_obs.id,
            category=cat,
            severity=sev,
            description=desc,
            compliance_status=ComplianceStatus.NON_COMPLIANT,
        )
        db.add(v_vio)
        await db.flush()

        v_task = Task(
            reference_number=_ref("TSK"),
            mine_id=mine_a.id,
            violation_id=v_vio.id,
            title=f"[HIGH] {cat.value} Issue",
            description=desc,
            category=cat,
            priority=TaskPriority.HIGH,
            status=random.choice([TaskStatus.OPEN, TaskStatus.ASSIGNED, TaskStatus.IN_PROGRESS]),
            assignee_id=field_officer2.id,
            assigned_by_id=manager_a.id,
            due_date=_dt(days_ago_insp - 7),
        )
        db.add(v_task)
        await db.flush()

    # ── MEDIUM violations (14 target) ──
    medium_violations = [
        "Missing safety signage at shaft entrance",
        "Equipment maintenance log incomplete for loader #7",
        "Worker training record not updated for 3 months",
        "Drainage channel partially blocked",
        "Vehicle inspection record missing for dumper #12",
        "Dust suppression not operational in transport road",
        "Emergency contact list outdated",
        "Gas detector calibration overdue",
        "Manual handling training incomplete",
        "First aid training attendance below 80%",
        "Environmental monitoring report delayed by 2 weeks",
        "Noise level measurement not conducted this quarter",
        "Spill kit not replenished after last incident",
        "Emergency drill not conducted in 60 days",
    ]

    for i, desc in enumerate(medium_violations):
        m_insp = Inspection(
            reference_number=_ref("INS"),
            mine_id=mine_a.id,
            inspector_id=field_officer.id,
            inspection_type="routine",
            status=InspectionStatus.COMPLETED,
            started_at=_dt(random.randint(3, 25)),
            overall_compliance_score=0.88,
            sync_status=SyncStatus.SYNCED,
        )
        db.add(m_insp)
        await db.flush()

        m_obs = Observation(
            inspection_id=m_insp.id,
            description=desc,
            latitude=23.6250 + random.uniform(-0.02, 0.02),
            longitude=85.5140 + random.uniform(-0.02, 0.02),
        )
        db.add(m_obs)
        await db.flush()

        m_cat = random.choice(list(ViolationCategory))
        m_vio = Violation(
            reference_number=_ref("VIO"),
            mine_id=mine_a.id,
            inspection_id=m_insp.id,
            observation_id=m_obs.id,
            category=m_cat,
            severity=SeverityLevel.MEDIUM,
            description=desc,
            compliance_status=ComplianceStatus.NON_COMPLIANT,
        )
        db.add(m_vio)
        await db.flush()

        # ~50% of medium violations have pending tasks
        if i < 7:
            m_task = Task(
                reference_number=_ref("TSK"),
                mine_id=mine_a.id,
                violation_id=m_vio.id,
                title=f"[MEDIUM] {m_cat.value} — {desc[:50]}",
                description=desc,
                category=m_cat,
                priority=TaskPriority.MEDIUM,
                status=TaskStatus.OPEN,
                due_date=_dt(-7),  # Future due date
            )
            db.add(m_task)
            await db.flush()

    # ── Additional recurring risks (target: 3 total) ──
    recurring2 = RecurringRisk(
        mine_id=mine_a.id,
        zone_id=zone_transport.id,
        category=ViolationCategory.VENTILATION,
        occurrence_count=3,
        first_occurrence=_dt(28),
        last_occurrence=_dt(8),
        time_window_days=30,
        severity=SeverityLevel.HIGH,
        status="active",
        recommended_action="3 ventilation failures in 30 days. Comprehensive ventilation system audit required.",
        trend="stable",
    )
    recurring3 = RecurringRisk(
        mine_id=mine_a.id,
        zone_id=zone_extraction.id,
        category=ViolationCategory.DOCUMENTATION,
        occurrence_count=3,
        first_occurrence=_dt(29),
        last_occurrence=_dt(6),
        time_window_days=30,
        severity=SeverityLevel.MEDIUM,
        status="active",
        recommended_action="3 documentation violations in 30 days. Records management training required.",
        trend="stable",
    )
    db.add_all([recurring2, recurring3])
    await db.flush()

    # ── COMPLIANCE DOCUMENTS ──
    doc_types = [
        ("Mining Lease License", "license", 730, "AUTH-2024-ML-001"),
        ("Environmental Clearance", "environmental_clearance", 365, "EC-2024-JKH-042"),
        ("Fire Safety Certificate", "fire_safety", 365, "FSC-2024-RMG-007"),
        ("Electrical Safety Clearance", "electrical_clearance", 180, "ESC-2024-001"),
        ("Explosives License", "explosives_license", 365, "EXP-2024-RMG-003"),
        ("Water Usage Permit", "water_permit", 730, "WUP-2023-JKH-011"),
        ("Worker Safety Plan", "safety_plan", None, "WSP-2024-RMG-001"),
    ]

    for title, dtype, days_valid, ref_no in doc_types:
        expiry = None
        if days_valid:
            # Some documents expired, some expiring soon, some valid
            offset = random.choice([-30, 20, 180])  # expired, expiring, valid
            expiry = datetime.utcnow() + timedelta(days=offset)

        from app.rules.engine import rule_engine
        doc_check = rule_engine.check_document_compliance(
            issue_date=datetime.utcnow() - timedelta(days=365),
            expiry_date=expiry,
        )

        doc = ComplianceDocument(
            mine_id=mine_a.id,
            title=title,
            document_type=dtype,
            reference_number=ref_no,
            issue_date=datetime.utcnow() - timedelta(days=365),
            expiry_date=expiry,
            compliance_status=ComplianceStatus(doc_check["status"].replace("warning", "warning").replace("expired", "expired").replace("compliant", "compliant").replace("pending_review", "pending_review")),
            ocr_status="complete",
            uploaded_by_id=compliance_officer.id,
        )
        db.add(doc)

    # Add 93 more documents across mines
    for i in range(93):
        doc = ComplianceDocument(
            mine_id=random.choice([mine_a.id] + [m.id for m in other_mines[:4]]),
            title=f"Compliance Document {i+8}",
            document_type=random.choice(["permit", "license", "safety_plan", "certificate"]),
            compliance_status=random.choice(list(ComplianceStatus)),
            uploaded_by_id=compliance_officer.id,
            ocr_status=random.choice(["complete", "pending"]),
        )
        db.add(doc)
    await db.flush()

    # ── INSPECTIONS FOR OTHER MINES (bulk, for realism) ──
    for mine in other_mines[:5]:
        for j in range(20):
            bulk_insp = Inspection(
                reference_number=_ref("INS"),
                mine_id=mine.id,
                inspector_id=random.choice(extra_users[:10]).id,
                inspection_type=random.choice(["routine", "special", "follow_up"]),
                status=random.choice(list(InspectionStatus)),
                started_at=_dt(random.randint(1, 90)),
                overall_compliance_score=random.uniform(0.60, 0.98),
                sync_status=SyncStatus.SYNCED,
            )
            db.add(bulk_insp)
        await db.flush()

        for j in range(10):
            bulk_cat = random.choice(list(ViolationCategory))
            bulk_sev = random.choice(list(SeverityLevel))
            bulk_insp_ref = Inspection(
                reference_number=_ref("INS"),
                mine_id=mine.id,
                inspector_id=random.choice(extra_users[:10]).id,
                inspection_type="routine",
                status=InspectionStatus.COMPLETED,
                started_at=_dt(random.randint(1, 30)),
                overall_compliance_score=random.uniform(0.60, 0.95),
                sync_status=SyncStatus.SYNCED,
            )
            db.add(bulk_insp_ref)
            await db.flush()

            bulk_vio = Violation(
                reference_number=_ref("VIO"),
                mine_id=mine.id,
                inspection_id=bulk_insp_ref.id,
                category=bulk_cat,
                severity=bulk_sev,
                description=f"Violation: {bulk_cat.value} issue detected during routine inspection.",
                compliance_status=ComplianceStatus.NON_COMPLIANT,
            )
            db.add(bulk_vio)
        await db.flush()

    logger.info("✅ Seed data created successfully.")
    logger.info(f"   Demo credentials:")
    logger.info(f"   Admin:      admin@coalmine.gov.in / Admin@1234")
    logger.info(f"   Manager:    manager.a@coalmine.gov.in / Manager@1234")
    logger.info(f"   Compliance: compliance@coalmine.gov.in / Compliance@1234")
    logger.info(f"   Field:      field.officer@coalmine.gov.in / Field@1234")
    logger.info(f"   Corporate:  corporate@coalmine.gov.in / Corporate@1234")
