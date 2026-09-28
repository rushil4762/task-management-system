from datetime import datetime, timezone
from sqlalchemy import case, delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task, TaskPriority, TaskStatus


async def create_task(
    db: AsyncSession,
    task: Task,
) -> Task:
    try:
        db.add(task)
        await db.commit()
        await db.refresh(task)
        return task
    except Exception:
        await db.rollback()
        raise


async def get_task_by_id(
    db: AsyncSession,
    task_id: int,
    user_id: int | None = None,
) -> Task | None:
    query = select(Task).where(Task.id == task_id)
    if user_id is not None:
        query = query.where(Task.user_id == user_id)

    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_tasks(
    db: AsyncSession,
    user_id: int | None = None,
    limit: int = 10,
    offset: int = 0,
    search: str | None = None,
    status: TaskStatus | None = None,
    priority: TaskPriority | None = None,
    due_date_from: datetime | None = None,
    due_date_to: datetime | None = None,
    is_overdue: bool | None = None,
    is_completed: bool | None = None,
    sort_by: str = "created_at",
    order: str = "desc",
) -> tuple[list[Task], int]:
    # Build shared filter conditions scoped to user
    filters = []
    if user_id is not None:
        filters.append(Task.user_id == user_id)

    # Search in title or description
    if search and search.strip():
        term = f"%{search.strip()}%"
        filters.append(
            or_(
                Task.title.ilike(term),
                Task.description.ilike(term),
            )
        )

    # Status & Priority filters
    if status is not None:
        filters.append(Task.status == status)
    if priority is not None:
        filters.append(Task.priority == priority)

    # Due date range filters
    if due_date_from is not None:
        filters.append(Task.due_date >= due_date_from)
    if due_date_to is not None:
        filters.append(Task.due_date <= due_date_to)

    # Completion status filter
    if is_completed is not None:
        if is_completed:
            filters.append(Task.status == TaskStatus.COMPLETED)
        else:
            filters.append(Task.status != TaskStatus.COMPLETED)

    # Overdue filter (calculated based on current UTC timestamp and non-finished status)
    if is_overdue is not None:
        now = datetime.now(timezone.utc)
        if is_overdue:
            filters.append(Task.due_date.isnot(None))
            filters.append(Task.due_date < now)
            filters.append(Task.status.notin_([TaskStatus.COMPLETED, TaskStatus.CANCELLED]))
        else:
            filters.append(
                or_(
                    Task.due_date.is_(None),
                    Task.due_date >= now,
                    Task.status.in_([TaskStatus.COMPLETED, TaskStatus.CANCELLED]),
                )
            )

    # 1. Total count query with filters applied
    count_query = select(func.count(Task.id))
    if filters:
        count_query = count_query.where(*filters)

    count_result = await db.execute(count_query)
    total = count_result.scalar_one()

    # 2. Main data query
    query = select(Task)
    if filters:
        query = query.where(*filters)

    # Natural priority order mapping
    priority_order = case(
        (Task.priority == TaskPriority.LOW, 1),
        (Task.priority == TaskPriority.MEDIUM, 2),
        (Task.priority == TaskPriority.HIGH, 3),
        (Task.priority == TaskPriority.URGENT, 4),
        else_=5,
    )

    # Allowed sorting fields
    sort_columns = {
        "id": Task.id,
        "title": Task.title,
        "status": Task.status,
        "priority": priority_order,
        "due_date": Task.due_date,
        "completed_at": Task.completed_at,
        "created_at": Task.created_at,
        "updated_at": Task.updated_at,
    }

    sort_target = sort_columns.get(
        str(sort_by).lower(),
        Task.created_at,
    )

    is_asc = str(order).lower() == "asc"
    if sort_target is Task.due_date:
        order_clause = sort_target.asc().nulls_last() if is_asc else sort_target.desc().nulls_last()
    elif hasattr(sort_target, "asc"):
        order_clause = sort_target.asc() if is_asc else sort_target.desc()
    else:
        order_clause = sort_target.asc() if is_asc else sort_target.desc()

    # Apply ordering and pagination
    query = query.order_by(order_clause).limit(limit).offset(offset)

    result = await db.execute(query)
    tasks = list(result.scalars().all())

    return tasks, total


async def update_task(
    db: AsyncSession,
    task: Task,
) -> Task:
    try:
        await db.commit()
        await db.refresh(task)
        return task
    except Exception:
        await db.rollback()
        raise


async def delete_task(
    db: AsyncSession,
    task: Task,
) -> None:
    try:
        await db.delete(task)
        await db.commit()
    except Exception:
        await db.rollback()
        raise


async def delete_tasks_bulk(
    db: AsyncSession,
    task_ids: list[int],
    user_id: int,
) -> int:
    try:
        stmt = (
            delete(Task)
            .where(
                Task.id.in_(task_ids),
                Task.user_id == user_id,
            )
        )
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount
    except Exception:
        await db.rollback()
        raise