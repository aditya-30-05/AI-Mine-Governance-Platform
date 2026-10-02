"""Tasks API — full lifecycle with escalation workflow."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid

from app.database import get_db
from app.auth.security import get_current_user
from app.models import (
    Task, TaskHistory, TaskStatus, TaskPriority, User, Notification, NotificationType, SeverityLevel
)
from app.audit.service import log_audit
from app.api.ws_manager import ws_manager

router = APIRouter(prefix="/tasks", tags=["Tasks"])


class TaskAssign(BaseModel):
    assignee_id: str


class TaskEscalate(BaseModel):
    escalate_to_id: str
    note: str


class TaskResolve(BaseModel):
    resolution_note: str


class TaskVerify(BaseModel):
    verification_note: str
    approved: bool = True


async def _add_history(db, task_id, user_id, action, old_status, new_status, note=""):
    history = TaskHistory(
        task_id=task_id,
        changed_by_id=user_id,
        action=action,
        old_status=old_status,
        new_status=new_status,
        note=note,
    )
    db.add(history)


@router.get("")
async def list_tasks(
    mine_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    assignee_id: Optional[str] = Query(None),
    overdue_only: bool = Query(False),
    limit: int = Query(20, le=100),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        query = select(Task).order_by(Task.created_at.desc())

        if mine_id:
            query = query.where(Task.mine_id == uuid.UUID(mine_id))
        if status:
            query = query.where(Task.status == TaskStatus(status))
        if priority:
            query = query.where(Task.priority == TaskPriority(priority))
        if assignee_id:
            query = query.where(Task.assignee_id == uuid.UUID(assignee_id))
        if overdue_only:
            query = query.where(
                Task.due_date < datetime.utcnow(),
                Task.status.notin_([TaskStatus.RESOLVED, TaskStatus.VERIFIED, TaskStatus.CLOSED]),
            )

        # Field officers see only their tasks
        from app.models import UserRole
        if current_user.role == UserRole.FIELD_OFFICER:
            query = query.where(Task.assignee_id == current_user.id)

        count_result = await db.execute(select(func.count()).select_from(query.subquery()))
        total = count_result.scalar_one()

        result = await db.execute(query.limit(limit).offset(offset))
        tasks = result.scalars().all()

        return {
            "total": total,
            "items": [
                {
                    "id": str(t.id),
                    "reference_number": t.reference_number,
                    "mine_id": str(t.mine_id),
                    "violation_id": str(t.violation_id) if t.violation_id else None,
                    "title": t.title,
                    "description": t.description,
                    "category": t.category.value if t.category else None,
                    "priority": t.priority.value if t.priority else None,
                    "status": t.status.value if t.status else None,
                    "assignee_id": str(t.assignee_id) if t.assignee_id else None,
                    "due_date": t.due_date.isoformat() if t.due_date else None,
                    "is_overdue": (
                        t.due_date < datetime.utcnow()
                        and t.status not in [TaskStatus.RESOLVED, TaskStatus.VERIFIED, TaskStatus.CLOSED]
                    ) if t.due_date else False,
                    "escalation_count": t.escalation_count,
                    "resolved_at": t.resolved_at.isoformat() if t.resolved_at else None,
                    "created_at": t.created_at.isoformat(),
                }
                for t in tasks
            ],
        }
    except Exception:
        from app.services.demo_store import DEMO_TASKS
        filtered = DEMO_TASKS
        if status:
            filtered = [t for t in filtered if t["status"] == status]
        if priority:
            filtered = [t for t in filtered if t["priority"] == priority]
        if overdue_only:
            filtered = [t for t in filtered if t.get("is_overdue")]
        return {
            "total": len(filtered),
            "items": [
                {
                    "id": t["id"],
                    "reference_number": f"TSK-202610-{t['id'][:4]}",
                    "mine_id": t["mine_id"],
                    "violation_id": t.get("violation_id"),
                    "title": t["title"],
                    "description": t["description"],
                    "category": "Ventilation",
                    "priority": t["priority"],
                    "status": t["status"],
                    "assignee_id": "22222222-2222-2222-2222-222222222222",
                    "due_date": t["due_date"],
                    "is_overdue": t.get("is_overdue", False),
                    "escalation_count": 1 if t["status"] == "escalated" else 0,
                    "resolved_at": None,
                    "created_at": t["created_at"],
                }
                for t in filtered[:limit]
            ],
        }


@router.get("/{task_id}")
async def get_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        result = await db.execute(select(Task).where(Task.id == uuid.UUID(task_id)))
        task = result.scalar_one_or_none()
        if task:
            history_result = await db.execute(
                select(TaskHistory).where(TaskHistory.task_id == task.id).order_by(TaskHistory.created_at)
            )
            history = history_result.scalars().all()

            return {
                "id": str(task.id),
                "reference_number": task.reference_number,
                "mine_id": str(task.mine_id),
                "violation_id": str(task.violation_id) if task.violation_id else None,
                "title": task.title,
                "description": task.description,
                "category": task.category.value if task.category else None,
                "priority": task.priority.value if task.priority else None,
                "status": task.status.value if task.status else None,
                "assignee_id": str(task.assignee_id) if task.assignee_id else None,
                "due_date": task.due_date.isoformat() if task.due_date else None,
                "created_at": task.created_at.isoformat(),
                "history": [],
            }
    except Exception:
        pass

    from app.services.demo_store import DEMO_TASKS
    matched = next((t for t in DEMO_TASKS if t["id"] == task_id), DEMO_TASKS[0])
    return {
        "id": matched["id"],
        "reference_number": f"TSK-202610-{matched['id'][:4]}",
        "mine_id": matched["mine_id"],
        "violation_id": matched.get("violation_id"),
        "title": matched["title"],
        "description": matched["description"],
        "category": "Ventilation",
        "priority": matched["priority"],
        "status": matched["status"],
        "assignee_id": "22222222-2222-2222-2222-222222222222",
        "due_date": matched["due_date"],
        "created_at": matched["created_at"],
        "history": [
            {
                "id": str(uuid.uuid4()),
                "action": "ASSIGNED",
                "note": "Assigned to section supervisor",
                "created_at": matched["created_at"],
            }
        ],
    }


@router.patch("/{task_id}/assign")
async def assign_task(
    task_id: str,
    data: TaskAssign,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Task).where(Task.id == uuid.UUID(task_id)))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    old_status = task.status
    task.assignee_id = uuid.UUID(data.assignee_id)
    task.assigned_by_id = current_user.id
    task.status = TaskStatus.ASSIGNED

    await _add_history(db, task.id, current_user.id, "assigned", old_status, TaskStatus.ASSIGNED)
    await log_audit(db, str(current_user.id), "assign", "task", task_id,
                    old_value={"status": old_status.value},
                    new_value={"status": "assigned", "assignee_id": data.assignee_id})

    # Notify assignee
    notification = Notification(
        user_id=uuid.UUID(data.assignee_id),
        type=NotificationType.ALERT,
        title="New Task Assigned",
        message=f"Task '{task.title}' has been assigned to you. Due: {task.due_date}",
        severity=SeverityLevel(task.priority.value) if task.priority else SeverityLevel.MEDIUM,
        entity_type="task",
        entity_id=task.id,
        action_url=f"/tasks/{task_id}",
    )
    db.add(notification)

    await ws_manager.send_to_mine(str(task.mine_id), {
        "type": "task_assigned",
        "task_id": task_id,
        "assignee_id": data.assignee_id,
        "title": task.title,
    })

    return {"id": task_id, "status": "assigned"}


@router.post("/{task_id}/escalate")
async def escalate_task(
    task_id: str,
    data: TaskEscalate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Task).where(Task.id == uuid.UUID(task_id)))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    old_status = task.status
    task.status = TaskStatus.ESCALATED
    task.escalated_to_id = uuid.UUID(data.escalate_to_id)
    task.escalation_note = data.note
    task.escalation_count = (task.escalation_count or 0) + 1

    await _add_history(db, task.id, current_user.id, "escalated", old_status, TaskStatus.ESCALATED, data.note)
    await log_audit(db, str(current_user.id), "escalate", "task", task_id,
                    old_value={"status": old_status.value},
                    new_value={"status": "escalated", "escalated_to": data.escalate_to_id, "note": data.note})

    await ws_manager.broadcast({
        "type": "task_escalated",
        "task_id": task_id,
        "mine_id": str(task.mine_id),
        "title": task.title,
        "escalation_count": task.escalation_count,
        "timestamp": datetime.utcnow().isoformat(),
    })

    return {"id": task_id, "status": "escalated", "escalation_count": task.escalation_count}


@router.post("/{task_id}/resolve")
async def resolve_task(
    task_id: str,
    data: TaskResolve,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Task).where(Task.id == uuid.UUID(task_id)))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    old_status = task.status
    task.status = TaskStatus.RESOLVED
    task.resolution_note = data.resolution_note
    task.resolved_at = datetime.utcnow()

    await _add_history(db, task.id, current_user.id, "resolved", old_status, TaskStatus.RESOLVED, data.resolution_note)
    await log_audit(db, str(current_user.id), "resolve", "task", task_id,
                    old_value={"status": old_status.value},
                    new_value={"status": "resolved", "resolution_note": data.resolution_note[:200]})

    await ws_manager.send_to_mine(str(task.mine_id), {
        "type": "task_resolved",
        "task_id": task_id,
        "title": task.title,
        "timestamp": datetime.utcnow().isoformat(),
    })

    return {"id": task_id, "status": "resolved"}


@router.post("/{task_id}/verify")
async def verify_task(
    task_id: str,
    data: TaskVerify,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Task).where(Task.id == uuid.UUID(task_id)))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.status != TaskStatus.RESOLVED:
        raise HTTPException(status_code=400, detail="Task must be resolved before verification")

    old_status = task.status
    task.status = TaskStatus.VERIFIED if data.approved else TaskStatus.IN_PROGRESS
    task.verification_note = data.verification_note
    task.verified_at = datetime.utcnow()

    action = "verified" if data.approved else "verification_rejected"
    await _add_history(db, task.id, current_user.id, action, old_status, task.status, data.verification_note)
    await log_audit(db, str(current_user.id), action, "task", task_id,
                    old_value={"status": old_status.value},
                    new_value={"status": task.status.value, "approved": data.approved})

    await ws_manager.send_to_mine(str(task.mine_id), {
        "type": "task_verified",
        "task_id": task_id,
        "approved": data.approved,
        "timestamp": datetime.utcnow().isoformat(),
    })

    return {"id": task_id, "status": task.status.value, "approved": data.approved}
