from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity import TaskActivity
from app.models.task import TaskPriority, TaskStatus
from app.models.user import UserRole
from app.repositories import activity_repository, task_repository


def format_status_label(status_val: str | TaskStatus | None) -> str:
    if not status_val:
        return ""
    val = status_val.value if hasattr(status_val, "value") else str(status_val)
    mapping = {
        "pending": "Pending",
        "in_progress": "In Progress",
        "completed": "Completed",
        "cancelled": "Cancelled",
    }
    return mapping.get(val.lower(), val.replace("_", " ").title())


def format_priority_label(priority_val: str | TaskPriority | None) -> str:
    if not priority_val:
        return ""
    val = priority_val.value if hasattr(priority_val, "value") else str(priority_val)
    mapping = {
        "low": "Low",
        "medium": "Medium",
        "high": "High",
        "urgent": "Urgent",
    }
    return mapping.get(val.lower(), val.replace("_", " ").title())


def format_activity_date(dt: datetime | str | None) -> str:
    if dt is None:
        return ""
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
        except Exception:
            return dt
    return f"{dt.day} {dt.strftime('%b')}"


def are_datetimes_equal(d1: datetime | None, d2: datetime | None) -> bool:
    if d1 is None and d2 is None:
        return True
    if d1 is None or d2 is None:
        return False
    if d1.tzinfo is not None and d2.tzinfo is None:
        d2 = d2.replace(tzinfo=timezone.utc)
    elif d1.tzinfo is None and d2.tzinfo is not None:
        d1 = d1.replace(tzinfo=timezone.utc)
    return d1 == d2


def build_due_date_message(
    actor_name: str,
    old_due: datetime | str | None,
    new_due: datetime | str | None,
) -> str:
    old_str = format_activity_date(old_due)
    new_str = format_activity_date(new_due)
    if old_str and new_str:
        return f"{actor_name} changed due date from {old_str} to {new_str}"
    if new_str:
        return f"{actor_name} set due date to {new_str}"
    if old_str:
        return f"{actor_name} removed due date"
    return f"{actor_name} changed due date"


def build_category_message(
    actor_name: str,
    old_cat: str | None,
    new_cat: str | None,
) -> str:
    if old_cat and new_cat:
        return f"{actor_name} changed category from {old_cat} to {new_cat}"
    if new_cat:
        return f"{actor_name} set category to {new_cat}"
    if old_cat:
        return f"{actor_name} removed category"
    return f"{actor_name} changed category"


def build_assignment_message(
    actor_name: str,
    assignee_name: str | None,
) -> str:
    if assignee_name:
        return f"{actor_name} assigned task to {assignee_name}"
    return f"{actor_name} unassigned task"


def build_status_message(
    actor_name: str,
    old_status: Any,
    new_status: Any,
) -> str:
    return f"{actor_name} changed status from {format_status_label(old_status)} to {format_status_label(new_status)}"


def build_priority_message(
    actor_name: str,
    old_priority: Any,
    new_priority: Any,
) -> str:
    return f"{actor_name} changed priority from {format_priority_label(old_priority)} to {format_priority_label(new_priority)}"


async def get_activities_for_task(
    db: AsyncSession,
    task_id: int,
    user_id: int,
    role: UserRole = UserRole.CEO,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[TaskActivity], int]:
    # Authorize: user must have access to task
    if role == UserRole.EMPLOYEE:
        task = await task_repository.get_task_by_id(db=db, task_id=task_id)
        if task is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )
        if task.assigned_to_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: You cannot access tasks not assigned to you",
            )
    else:
        task = await task_repository.get_task_by_id(
            db=db,
            task_id=task_id,
            user_id=user_id,
            allow_assigned=True,
        )
        if task is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )

    return await activity_repository.get_activities_by_task_id(
        db=db,
        task_id=task_id,
        limit=limit,
        offset=offset,
    )


async def get_recent_activities_for_user(
    db: AsyncSession,
    user_id: int,
    limit: int = 10,
    offset: int = 0,
) -> tuple[list[TaskActivity], int]:
    return await activity_repository.get_recent_activities_for_user(
        db=db,
        user_id=user_id,
        limit=limit,
        offset=offset,
    )
