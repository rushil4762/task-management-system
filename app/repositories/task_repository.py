from sqlalchemy import func, select
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
    status: TaskStatus | None = None,
    priority: TaskPriority | None = None,
    sort_by: str = "created_at",
    order: str = "desc",
) -> tuple[list[Task], int]:
    # Build shared filter conditions scoped to user
    filters = []
    if user_id is not None:
        filters.append(Task.user_id == user_id)
    if status is not None:
        filters.append(Task.status == status)
    if priority is not None:
        filters.append(Task.priority == priority)

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

    # Allowed sorting fields
    sort_columns = {
        "id": Task.id,
        "title": Task.title,
        "status": Task.status,
        "priority": Task.priority,
        "created_at": Task.created_at,
        "updated_at": Task.updated_at,
    }

    sort_column = sort_columns.get(
        str(sort_by).lower(),
        Task.created_at,
    )

    if str(order).lower() == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    # Pagination
    query = query.limit(limit).offset(offset)

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