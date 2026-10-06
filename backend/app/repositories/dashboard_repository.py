from datetime import date, datetime, time, timedelta, timezone
from typing import Any

from sqlalchemy import and_, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.models.task import Task, TaskPriority, TaskStatus


async def get_task_metrics(
    db: AsyncSession,
    user_id: int,
    is_employee: bool = False,
) -> dict[str, Any]:
    """
    Execute a single database-level aggregate query computing task status counts,
    priority breakdown, and due date urgency metrics for the specified user.
    """
    now_utc = datetime.now(timezone.utc)
    start_of_today = datetime.combine(now_utc.date(), time.min, tzinfo=timezone.utc)
    end_of_today = datetime.combine(now_utc.date(), time.max, tzinfo=timezone.utc)
    end_of_week = start_of_today + timedelta(days=7)

    task_user_filter = Task.assigned_to_id == user_id if is_employee else Task.user_id == user_id

    stmt = select(
        func.count(Task.id).label("total"),
        func.count(case((Task.status == TaskStatus.PENDING, 1))).label("pending"),
        func.count(case((Task.status == TaskStatus.IN_PROGRESS, 1))).label("in_progress"),
        func.count(case((Task.status == TaskStatus.COMPLETED, 1))).label("completed"),
        func.count(case((Task.status == TaskStatus.CANCELLED, 1))).label("cancelled"),
        func.count(case((Task.priority == TaskPriority.LOW, 1))).label("priority_low"),
        func.count(case((Task.priority == TaskPriority.MEDIUM, 1))).label("priority_medium"),
        func.count(case((Task.priority == TaskPriority.HIGH, 1))).label("priority_high"),
        func.count(case((Task.priority == TaskPriority.URGENT, 1))).label("priority_urgent"),
        func.count(
            case(
                (
                    and_(
                        Task.due_date.isnot(None),
                        Task.due_date < now_utc,
                        Task.status.notin_([TaskStatus.COMPLETED, TaskStatus.CANCELLED]),
                    ),
                    1,
                )
            )
        ).label("overdue"),
        func.count(
            case(
                (
                    and_(
                        Task.due_date.isnot(None),
                        Task.due_date >= start_of_today,
                        Task.due_date <= end_of_today,
                        Task.status.notin_([TaskStatus.COMPLETED, TaskStatus.CANCELLED]),
                    ),
                    1,
                )
            )
        ).label("due_today"),
        func.count(
            case(
                (
                    and_(
                        Task.due_date.isnot(None),
                        Task.due_date >= start_of_today,
                        Task.due_date <= end_of_week,
                        Task.status.notin_([TaskStatus.COMPLETED, TaskStatus.CANCELLED]),
                    ),
                    1,
                )
            )
        ).label("due_this_week"),
        func.count(
            case(
                (
                    and_(
                        Task.due_date.isnot(None),
                        Task.due_date > end_of_today,
                        Task.status.notin_([TaskStatus.COMPLETED, TaskStatus.CANCELLED]),
                    ),
                    1,
                )
            )
        ).label("upcoming"),
    ).where(task_user_filter)

    result = await db.execute(stmt)
    row = result.mappings().one()

    total = row["total"] or 0
    completed = row["completed"] or 0
    completion_percentage = round((completed / total) * 100.0, 2) if total > 0 else 0.0

    return {
        "status": {
            "total": total,
            "pending": row["pending"] or 0,
            "in_progress": row["in_progress"] or 0,
            "completed": completed,
            "cancelled": row["cancelled"] or 0,
        },
        "priorities": {
            "low": row["priority_low"] or 0,
            "medium": row["priority_medium"] or 0,
            "high": row["priority_high"] or 0,
            "urgent": row["priority_urgent"] or 0,
        },
        "due_dates": {
            "overdue": row["overdue"] or 0,
            "due_today": row["due_today"] or 0,
            "due_this_week": row["due_this_week"] or 0,
            "upcoming": row["upcoming"] or 0,
        },
        "completion": {
            "total_completed": completed,
            "completion_percentage": completion_percentage,
        },
    }


async def get_category_metrics(
    db: AsyncSession,
    user_id: int,
    is_employee: bool = False,
) -> list[dict[str, Any]]:
    """
    Return task counts grouped by category for the specified user.
    Also includes uncategorized tasks if any exist.
    """
    task_user_filter = Task.assigned_to_id == user_id if is_employee else Task.user_id == user_id

    stmt = (
        select(
            Category.id.label("category_id"),
            Category.name.label("category_name"),
            func.count(Task.id).label("task_count"),
        )
        .outerjoin(
            Task,
            and_(
                Task.category_id == Category.id,
                task_user_filter,
            ),
        )
    )
    if not is_employee:
        stmt = stmt.where(Category.user_id == user_id)
    stmt = stmt.group_by(Category.id, Category.name).order_by(Category.name.asc())

    result = await db.execute(stmt)
    category_counts = [
        {
            "category_id": row.category_id,
            "category_name": row.category_name,
            "task_count": row.task_count,
        }
        for row in result.all()
    ]

    uncategorized_stmt = select(func.count(Task.id)).where(
        task_user_filter,
        Task.category_id.is_(None),
    )
    uncategorized_res = await db.execute(uncategorized_stmt)
    uncategorized_count = uncategorized_res.scalar_one()

    if uncategorized_count > 0:
        category_counts.append(
            {
                "category_id": None,
                "category_name": "Uncategorized",
                "task_count": uncategorized_count,
            }
        )

    return category_counts


async def get_completion_trend(
    db: AsyncSession,
    user_id: int,
    start_date: date | None = None,
    end_date: date | None = None,
    is_employee: bool = False,
) -> list[dict[str, Any]]:
    """
    Aggregate completed tasks grouped by date using database-level grouping.
    Optionally filters within [start_date, end_date].
    """
    date_col = func.date(Task.completed_at)
    task_user_filter = Task.assigned_to_id == user_id if is_employee else Task.user_id == user_id
    query = (
        select(
            date_col.label("date"),
            func.count(Task.id).label("completed"),
        )
        .where(
            task_user_filter,
            Task.status == TaskStatus.COMPLETED,
            Task.completed_at.isnot(None),
        )
    )

    if start_date is not None:
        start_dt = datetime.combine(start_date, time.min, tzinfo=timezone.utc)
        query = query.where(Task.completed_at >= start_dt)
    if end_date is not None:
        end_dt = datetime.combine(end_date, time.max, tzinfo=timezone.utc)
        query = query.where(Task.completed_at <= end_dt)

    query = query.group_by(date_col).order_by(date_col.asc())
    result = await db.execute(query)

    return [
        {
            "date": str(row.date),
            "completed": row.completed,
        }
        for row in result.all()
    ]
