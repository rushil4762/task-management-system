from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.notification import NotificationType
from app.models.task import Task, TaskStatus
from app.services import notification_service


async def check_and_create_due_soon_reminders(db: AsyncSession) -> int:
    """
    Find active tasks whose due date falls within the configured due-soon window
    and create notifications for task owners and assignees.
    Duplicate checks ensure repeated runs do not duplicate notifications for the same due date.
    """
    now = datetime.now(timezone.utc)
    window_end = now + timedelta(hours=settings.TASK_DUE_SOON_HOURS)

    stmt = select(Task).where(
        Task.status.notin_([TaskStatus.COMPLETED, TaskStatus.CANCELLED]),
        Task.due_date.isnot(None),
        Task.due_date >= now,
        Task.due_date <= window_end,
    )
    result = await db.execute(stmt)
    tasks = list(result.scalars().all())

    created_count = 0
    for task in tasks:
        if task.due_date is None:
            continue

        recipients: set[int] = {task.user_id}
        if task.assigned_to_id is not None:
            recipients.add(task.assigned_to_id)

        due_str = task.due_date.strftime("%Y-%m-%d %H:%M UTC")
        event_key = f"due_soon_{task.due_date.isoformat()}"

        for recipient_id in recipients:
            notif = await notification_service.create_notification(
                db=db,
                user_id=recipient_id,
                task_id=task.id,
                type=NotificationType.TASK_DUE_SOON,
                title=f"Task Due Soon: {task.title}",
                message=f"Task '{task.title}' is due soon on {due_str}.",
                event_key=event_key,
            )
            if notif is not None:
                created_count += 1

    return created_count


async def check_and_create_overdue_reminders(db: AsyncSession) -> int:
    """
    Find active tasks whose due date has passed (excluding completed and cancelled tasks)
    and create notifications for task owners and assignees.
    Duplicate checks ensure repeated runs do not duplicate notifications for the same due date.
    """
    now = datetime.now(timezone.utc)

    stmt = select(Task).where(
        Task.status.notin_([TaskStatus.COMPLETED, TaskStatus.CANCELLED]),
        Task.due_date.isnot(None),
        Task.due_date < now,
    )
    result = await db.execute(stmt)
    tasks = list(result.scalars().all())

    created_count = 0
    for task in tasks:
        if task.due_date is None:
            continue

        recipients: set[int] = {task.user_id}
        if task.assigned_to_id is not None:
            recipients.add(task.assigned_to_id)

        due_str = task.due_date.strftime("%Y-%m-%d %H:%M UTC")
        event_key = f"overdue_{task.due_date.isoformat()}"

        for recipient_id in recipients:
            notif = await notification_service.create_notification(
                db=db,
                user_id=recipient_id,
                task_id=task.id,
                type=NotificationType.TASK_OVERDUE,
                title=f"Task Overdue: {task.title}",
                message=f"Task '{task.title}' was due on {due_str} and is now overdue.",
                event_key=event_key,
            )
            if notif is not None:
                created_count += 1

    return created_count


async def run_all_reminders(db: AsyncSession) -> dict[str, int]:
    """
    Execute all task reminder checks. Can be invoked directly or triggered by
    a background worker (such as Celery/cron).
    """
    due_soon = await check_and_create_due_soon_reminders(db=db)
    overdue = await check_and_create_overdue_reminders(db=db)
    return {
        "due_soon_reminders": due_soon,
        "overdue_reminders": overdue,
    }
