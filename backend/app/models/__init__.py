"""
SQLAlchemy models for Coal Mine Governance System.
All 16+ entities with proper relationships, indexes, and constraints.
"""
import uuid
from datetime import datetime
from typing import Optional
import enum

from sqlalchemy import (
    Column, String, Text, Boolean, Integer, Float, DateTime,
    ForeignKey, Enum, JSON, Index, UniqueConstraint, CheckConstraint,
    func, event
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship, declared_attr
from geoalchemy2 import Geometry

from app.database import Base


# ─────────────────────────────────────────────
# ENUMS
# ─────────────────────────────────────────────

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    FIELD_OFFICER = "field_officer"
    COMPLIANCE_OFFICER = "compliance_officer"
    MINE_MANAGER = "mine_manager"
    CORPORATE_MANAGER = "corporate_manager"


class InspectionStatus(str, enum.Enum):
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    COMPLETED = "completed"
    SYNCED = "synced"


class SeverityLevel(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class TaskStatus(str, enum.Enum):
    OPEN = "open"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    OVERDUE = "overdue"
    ESCALATED = "escalated"
    RESOLVED = "resolved"
    VERIFIED = "verified"
    CLOSED = "closed"


class TaskPriority(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ComplianceStatus(str, enum.Enum):
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    WARNING = "warning"
    PENDING_REVIEW = "pending_review"
    EXPIRED = "expired"


class ViolationCategory(str, enum.Enum):
    PPE = "PPE"
    FIRE_SAFETY = "Fire Safety"
    ELECTRICAL_SAFETY = "Electrical Safety"
    VENTILATION = "Ventilation"
    ENVIRONMENTAL = "Environmental"
    EQUIPMENT = "Equipment"
    LABOUR_WORKER_SAFETY = "Labour/Worker Safety"
    DOCUMENTATION = "Documentation"
    EMERGENCY_PREPAREDNESS = "Emergency Preparedness"


class SyncStatus(str, enum.Enum):
    PENDING = "pending"
    SYNCING = "syncing"
    SYNCED = "synced"
    FAILED = "failed"
    CONFLICT = "conflict"


class NotificationType(str, enum.Enum):
    ALERT = "alert"
    REMINDER = "reminder"
    ESCALATION = "escalation"
    INFO = "info"
    SYSTEM = "system"


# ─────────────────────────────────────────────
# MIXINS
# ─────────────────────────────────────────────

class TimestampMixin:
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class UUIDMixin:
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


# ─────────────────────────────────────────────
# SUBSIDIARY
# ─────────────────────────────────────────────

class Subsidiary(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "subsidiaries"

    name = Column(String(200), nullable=False, unique=True)
    code = Column(String(20), nullable=False, unique=True)
    state = Column(String(100))
    region = Column(String(100))
    is_active = Column(Boolean, default=True)

    mines = relationship("Mine", back_populates="subsidiary")


# ─────────────────────────────────────────────
# MINE
# ─────────────────────────────────────────────

class Mine(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "mines"

    name = Column(String(200), nullable=False)
    code = Column(String(20), nullable=False, unique=True)
    subsidiary_id = Column(UUID(as_uuid=True), ForeignKey("subsidiaries.id"), nullable=False)
    location_name = Column(String(200))
    state = Column(String(100))
    district = Column(String(100))
    # PostGIS geometry: center point
    location = Column(Geometry(geometry_type="POINT", srid=4326))
    latitude = Column(Float)
    longitude = Column(Float)
    mine_type = Column(String(50))  # opencast, underground
    capacity_mtpa = Column(Float)
    is_active = Column(Boolean, default=True)
    manager_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    subsidiary = relationship("Subsidiary", back_populates="mines")
    manager = relationship("User", foreign_keys=[manager_id])
    inspections = relationship("Inspection", back_populates="mine")
    violations = relationship("Violation", back_populates="mine")
    tasks = relationship("Task", back_populates="mine")
    compliance_documents = relationship("ComplianceDocument", back_populates="mine")
    zones = relationship("MineZone", back_populates="mine")

    __table_args__ = (
        Index("idx_mines_subsidiary", "subsidiary_id"),
        Index("idx_mines_code", "code"),
    )


# ─────────────────────────────────────────────
# MINE ZONE
# ─────────────────────────────────────────────

class MineZone(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "mine_zones"

    mine_id = Column(UUID(as_uuid=True), ForeignKey("mines.id"), nullable=False)
    name = Column(String(100), nullable=False)
    zone_type = Column(String(50))  # extraction, processing, storage, entry, etc.
    boundary = Column(Geometry(geometry_type="POLYGON", srid=4326))
    is_active = Column(Boolean, default=True)

    mine = relationship("Mine", back_populates="zones")
    observations = relationship("Observation", back_populates="zone")

    __table_args__ = (
        Index("idx_mine_zones_mine", "mine_id"),
    )


# ─────────────────────────────────────────────
# USER
# ─────────────────────────────────────────────

class User(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "users"

    employee_id = Column(String(50), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    full_name = Column(String(200), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.FIELD_OFFICER)
    phone = Column(String(20))
    department = Column(String(100))
    subsidiary_id = Column(UUID(as_uuid=True), ForeignKey("subsidiaries.id"), nullable=True)
    mine_id = Column(UUID(as_uuid=True), ForeignKey("mines.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime(timezone=True))
    preferred_language = Column(String(10), default="en")

    subsidiary = relationship("Subsidiary")
    mine = relationship("Mine", foreign_keys=[mine_id])
    inspections = relationship("Inspection", back_populates="inspector", foreign_keys="Inspection.inspector_id")
    assigned_tasks = relationship("Task", back_populates="assignee", foreign_keys="Task.assignee_id")
    notifications = relationship("Notification", back_populates="user")

    __table_args__ = (
        Index("idx_users_email", "email"),
        Index("idx_users_role", "role"),
        Index("idx_users_mine", "mine_id"),
    )


# ─────────────────────────────────────────────
# INSPECTION
# ─────────────────────────────────────────────

class Inspection(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "inspections"

    reference_number = Column(String(50), unique=True, nullable=False)
    mine_id = Column(UUID(as_uuid=True), ForeignKey("mines.id"), nullable=False)
    inspector_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    inspection_type = Column(String(50), nullable=False)  # routine, special, follow_up
    status = Column(Enum(InspectionStatus), default=InspectionStatus.DRAFT)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    scheduled_date = Column(DateTime(timezone=True))
    # GPS of inspection start
    start_location = Column(Geometry(geometry_type="POINT", srid=4326))
    start_latitude = Column(Float)
    start_longitude = Column(Float)
    notes = Column(Text)
    weather_conditions = Column(String(100))
    shift = Column(String(20))  # morning, afternoon, night
    # Offline sync fields
    client_id = Column(String(100), unique=True)  # UUID from client for dedup
    sync_status = Column(Enum(SyncStatus), default=SyncStatus.SYNCED)
    synced_at = Column(DateTime(timezone=True))
    device_id = Column(String(100))
    overall_compliance_score = Column(Float)

    mine = relationship("Mine", back_populates="inspections")
    inspector = relationship("User", back_populates="inspections", foreign_keys=[inspector_id])
    observations = relationship("Observation", back_populates="inspection", cascade="all, delete-orphan")
    violations = relationship("Violation", back_populates="inspection")

    __table_args__ = (
        Index("idx_inspections_mine", "mine_id"),
        Index("idx_inspections_inspector", "inspector_id"),
        Index("idx_inspections_status", "status"),
        Index("idx_inspections_created", "created_at"),
        Index("idx_inspections_client_id", "client_id"),
    )


# ─────────────────────────────────────────────
# OBSERVATION
# ─────────────────────────────────────────────

class Observation(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "observations"

    inspection_id = Column(UUID(as_uuid=True), ForeignKey("inspections.id"), nullable=False)
    zone_id = Column(UUID(as_uuid=True), ForeignKey("mine_zones.id"), nullable=True)
    category = Column(Enum(ViolationCategory))
    description = Column(Text, nullable=False)
    # GPS
    location = Column(Geometry(geometry_type="POINT", srid=4326))
    latitude = Column(Float)
    longitude = Column(Float)
    accuracy_meters = Column(Float)
    # Evidence
    photo_urls = Column(JSON, default=list)  # list of file paths
    audio_url = Column(String(500))
    # AI Analysis
    ai_analysis_id = Column(UUID(as_uuid=True), ForeignKey("ai_analysis.id"), nullable=True)
    # Offline
    client_id = Column(String(100))
    captured_at = Column(DateTime(timezone=True), server_default=func.now())

    inspection = relationship("Inspection", back_populates="observations")
    zone = relationship("MineZone", back_populates="observations")
    ai_analysis = relationship("AIAnalysis", back_populates="observation")
    violation = relationship("Violation", back_populates="observation", uselist=False)

    __table_args__ = (
        Index("idx_observations_inspection", "inspection_id"),
        Index("idx_observations_category", "category"),
    )


# ─────────────────────────────────────────────
# AI ANALYSIS
# ─────────────────────────────────────────────

class AIAnalysis(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "ai_analysis"

    observation_id = Column(UUID(as_uuid=True), nullable=True)  # back-ref from Observation
    input_text = Column(Text, nullable=False)
    model_used = Column(String(100))
    is_demo_fallback = Column(Boolean, default=False)  # True if AI unavailable
    # Structured output
    category = Column(String(100))
    severity = Column(Enum(SeverityLevel))
    risk_score = Column(Float)  # 0.0 to 1.0
    confidence = Column(Float)  # 0.0 to 1.0
    explanation = Column(Text)
    recommended_action = Column(Text)
    raw_response = Column(JSON)  # full LLM response
    # Rule engine override
    rule_adjusted = Column(Boolean, default=False)
    rule_adjustment_reason = Column(Text)
    # Human verification
    human_verified = Column(Boolean, default=False)
    verified_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    verified_at = Column(DateTime(timezone=True))
    verification_note = Column(Text)

    observation = relationship("Observation", back_populates="ai_analysis")
    verified_by = relationship("User")

    __table_args__ = (
        Index("idx_ai_analysis_severity", "severity"),
    )


# ─────────────────────────────────────────────
# VIOLATION
# ─────────────────────────────────────────────

class Violation(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "violations"

    reference_number = Column(String(50), unique=True, nullable=False)
    mine_id = Column(UUID(as_uuid=True), ForeignKey("mines.id"), nullable=False)
    inspection_id = Column(UUID(as_uuid=True), ForeignKey("inspections.id"), nullable=False)
    observation_id = Column(UUID(as_uuid=True), ForeignKey("observations.id"), nullable=True)
    category = Column(Enum(ViolationCategory), nullable=False)
    severity = Column(Enum(SeverityLevel), nullable=False)
    description = Column(Text, nullable=False)
    location = Column(Geometry(geometry_type="POINT", srid=4326))
    latitude = Column(Float)
    longitude = Column(Float)
    zone_id = Column(UUID(as_uuid=True), ForeignKey("mine_zones.id"), nullable=True)
    compliance_status = Column(Enum(ComplianceStatus), default=ComplianceStatus.NON_COMPLIANT)
    is_recurring = Column(Boolean, default=False)
    recurring_risk_id = Column(UUID(as_uuid=True), ForeignKey("recurring_risks.id"), nullable=True)
    resolved_at = Column(DateTime(timezone=True))
    resolution_note = Column(Text)
    photo_urls = Column(JSON, default=list)
    rule_ids = Column(JSON, default=list)  # compliance rules that were violated

    mine = relationship("Mine", back_populates="violations")
    inspection = relationship("Inspection", back_populates="violations")
    observation = relationship("Observation", back_populates="violation")
    zone = relationship("MineZone")
    task = relationship("Task", back_populates="violation", uselist=False)
    recurring_risk = relationship("RecurringRisk", back_populates="violations")

    __table_args__ = (
        Index("idx_violations_mine", "mine_id"),
        Index("idx_violations_category", "category"),
        Index("idx_violations_severity", "severity"),
        Index("idx_violations_created", "created_at"),
        Index("idx_violations_recurring", "is_recurring"),
    )


# ─────────────────────────────────────────────
# RECURRING RISK
# ─────────────────────────────────────────────

class RecurringRisk(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "recurring_risks"

    mine_id = Column(UUID(as_uuid=True), ForeignKey("mines.id"), nullable=False)
    zone_id = Column(UUID(as_uuid=True), ForeignKey("mine_zones.id"), nullable=True)
    category = Column(Enum(ViolationCategory), nullable=False)
    occurrence_count = Column(Integer, default=1)
    first_occurrence = Column(DateTime(timezone=True))
    last_occurrence = Column(DateTime(timezone=True))
    time_window_days = Column(Integer, default=30)
    severity = Column(Enum(SeverityLevel), default=SeverityLevel.HIGH)
    status = Column(String(20), default="active")  # active, resolved, monitoring
    recommended_action = Column(Text)
    trend = Column(String(20), default="stable")  # increasing, stable, decreasing
    center_location = Column(Geometry(geometry_type="POINT", srid=4326))
    location_radius_meters = Column(Float, default=500)

    mine = relationship("Mine")
    zone = relationship("MineZone")
    violations = relationship("Violation", back_populates="recurring_risk")

    __table_args__ = (
        Index("idx_recurring_mine", "mine_id"),
        Index("idx_recurring_category", "category"),
        Index("idx_recurring_status", "status"),
    )


# ─────────────────────────────────────────────
# COMPLIANCE RULE
# ─────────────────────────────────────────────

class ComplianceRule(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "compliance_rules"

    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    category = Column(Enum(ViolationCategory), nullable=False)
    description = Column(Text)
    regulation_reference = Column(String(200))  # e.g., "CMR 2017, Section 12"
    severity_if_violated = Column(Enum(SeverityLevel), default=SeverityLevel.MEDIUM)
    is_active = Column(Boolean, default=True)
    auto_escalate = Column(Boolean, default=False)
    escalation_threshold_hours = Column(Integer, default=24)
    recurring_threshold_count = Column(Integer, default=3)
    recurring_threshold_days = Column(Integer, default=30)

    __table_args__ = (
        Index("idx_rules_category", "category"),
    )


# ─────────────────────────────────────────────
# COMPLIANCE DOCUMENT
# ─────────────────────────────────────────────

class ComplianceDocument(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "compliance_documents"

    mine_id = Column(UUID(as_uuid=True), ForeignKey("mines.id"), nullable=True)
    title = Column(String(300), nullable=False)
    document_type = Column(String(100))  # license, permit, safety_plan, etc.
    file_path = Column(String(500))
    file_size_bytes = Column(Integer)
    mime_type = Column(String(100))
    reference_number = Column(String(100))
    issuing_authority = Column(String(200))
    issue_date = Column(DateTime(timezone=True))
    expiry_date = Column(DateTime(timezone=True))
    compliance_status = Column(Enum(ComplianceStatus), default=ComplianceStatus.PENDING_REVIEW)
    # OCR results
    ocr_status = Column(String(20), default="pending")  # pending, processing, complete, failed
    ocr_raw_text = Column(Text)
    ocr_structured = Column(JSON)
    ocr_confidence = Column(Float)
    human_corrected = Column(Boolean, default=False)
    # RAG embedding
    embedding_status = Column(String(20), default="pending")
    uploaded_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    mine = relationship("Mine", back_populates="compliance_documents")
    uploaded_by = relationship("User")

    __table_args__ = (
        Index("idx_docs_mine", "mine_id"),
        Index("idx_docs_expiry", "expiry_date"),
        Index("idx_docs_status", "compliance_status"),
    )


# ─────────────────────────────────────────────
# TASK
# ─────────────────────────────────────────────

class Task(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "tasks"

    reference_number = Column(String(50), unique=True, nullable=False)
    mine_id = Column(UUID(as_uuid=True), ForeignKey("mines.id"), nullable=False)
    violation_id = Column(UUID(as_uuid=True), ForeignKey("violations.id"), nullable=True)
    recurring_risk_id = Column(UUID(as_uuid=True), ForeignKey("recurring_risks.id"), nullable=True)
    title = Column(String(300), nullable=False)
    description = Column(Text)
    category = Column(Enum(ViolationCategory))
    priority = Column(Enum(TaskPriority), default=TaskPriority.MEDIUM)
    status = Column(Enum(TaskStatus), default=TaskStatus.OPEN)
    assignee_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    assigned_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    escalated_to_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    due_date = Column(DateTime(timezone=True))
    reminder_date = Column(DateTime(timezone=True))
    started_at = Column(DateTime(timezone=True))
    resolved_at = Column(DateTime(timezone=True))
    verified_at = Column(DateTime(timezone=True))
    closed_at = Column(DateTime(timezone=True))
    resolution_note = Column(Text)
    verification_note = Column(Text)
    escalation_note = Column(Text)
    escalation_count = Column(Integer, default=0)

    mine = relationship("Mine", back_populates="tasks")
    violation = relationship("Violation", back_populates="task")
    assignee = relationship("User", back_populates="assigned_tasks", foreign_keys=[assignee_id])
    assigned_by = relationship("User", foreign_keys=[assigned_by_id])
    escalated_to = relationship("User", foreign_keys=[escalated_to_id])
    history = relationship("TaskHistory", back_populates="task", order_by="TaskHistory.created_at")

    __table_args__ = (
        Index("idx_tasks_mine", "mine_id"),
        Index("idx_tasks_status", "status"),
        Index("idx_tasks_assignee", "assignee_id"),
        Index("idx_tasks_due", "due_date"),
        Index("idx_tasks_priority", "priority"),
    )


# ─────────────────────────────────────────────
# TASK HISTORY
# ─────────────────────────────────────────────

class TaskHistory(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "task_history"

    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False)
    changed_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    action = Column(String(50), nullable=False)  # created, assigned, escalated, resolved, etc.
    old_status = Column(Enum(TaskStatus))
    new_status = Column(Enum(TaskStatus))
    note = Column(Text)
    metadata_ = Column("metadata", JSON, default=dict)

    task = relationship("Task", back_populates="history")
    changed_by = relationship("User")

    __table_args__ = (
        Index("idx_task_history_task", "task_id"),
    )


# ─────────────────────────────────────────────
# NOTIFICATION
# ─────────────────────────────────────────────

class Notification(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "notifications"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    type = Column(Enum(NotificationType), default=NotificationType.INFO)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    severity = Column(Enum(SeverityLevel), default=SeverityLevel.INFO)
    entity_type = Column(String(50))  # task, violation, inspection, etc.
    entity_id = Column(UUID(as_uuid=True))
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime(timezone=True))
    action_url = Column(String(500))

    user = relationship("User", back_populates="notifications")

    __table_args__ = (
        Index("idx_notifications_user", "user_id"),
        Index("idx_notifications_read", "is_read"),
        Index("idx_notifications_created", "created_at"),
    )


# ─────────────────────────────────────────────
# AUDIT LOG
# ─────────────────────────────────────────────

class AuditLog(UUIDMixin, Base):
    __tablename__ = "audit_logs"

    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(UUID(as_uuid=True))
    old_value = Column(JSON)
    new_value = Column(JSON)
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    # Hash chain
    record_hash = Column(String(64), nullable=False)  # SHA-256 of this record
    previous_hash = Column(String(64))  # SHA-256 of previous audit entry for same entity

    user = relationship("User")

    __table_args__ = (
        Index("idx_audit_entity", "entity_type", "entity_id"),
        Index("idx_audit_user", "user_id"),
        Index("idx_audit_timestamp", "timestamp"),
        Index("idx_audit_action", "action"),
    )


# ─────────────────────────────────────────────
# SYNC QUEUE METADATA
# ─────────────────────────────────────────────

class SyncQueueMetadata(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "sync_queue_metadata"

    client_id = Column(String(100), unique=True, nullable=False)
    entity_type = Column(String(50), nullable=False)  # inspection, observation
    server_entity_id = Column(UUID(as_uuid=True))
    device_id = Column(String(100))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    status = Column(Enum(SyncStatus), default=SyncStatus.PENDING)
    payload_hash = Column(String(64))  # to detect duplicates
    attempts = Column(Integer, default=0)
    last_attempt = Column(DateTime(timezone=True))
    error_message = Column(Text)
    synced_at = Column(DateTime(timezone=True))

    __table_args__ = (
        Index("idx_sync_client", "client_id"),
        Index("idx_sync_status", "status"),
    )


# ─────────────────────────────────────────────
# REPORT JOB
# ─────────────────────────────────────────────

class ReportJob(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "report_jobs"

    mine_id = Column(UUID(as_uuid=True), ForeignKey("mines.id"), nullable=True)
    requested_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    report_type = Column(String(50), nullable=False)  # compliance, incident, trend
    parameters = Column(JSON, default=dict)
    status = Column(String(20), default="pending")  # pending, processing, complete, failed
    file_path = Column(String(500))
    error_message = Column(Text)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))

    mine = relationship("Mine")
    requested_by = relationship("User")


# ─────────────────────────────────────────────
# DOCUMENT CHUNK (for RAG)
# ─────────────────────────────────────────────

class DocumentChunk(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "document_chunks"

    document_id = Column(UUID(as_uuid=True), ForeignKey("compliance_documents.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    # pgvector embedding — stored as JSON array for compatibility
    # In production with pgvector: use Vector(1536) type
    embedding_json = Column(JSON)
    token_count = Column(Integer)
    metadata_ = Column("metadata", JSON, default=dict)

    document = relationship("ComplianceDocument")

    __table_args__ = (
        Index("idx_chunks_document", "document_id"),
    )
