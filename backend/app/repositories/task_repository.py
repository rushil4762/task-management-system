from datetime import datetime, timezone
from sqlalchemy import case, delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.models.category import Category
from app.models.tag import Tag
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
    allow_assigned: bool = False,
) -> Task | None:
    query = (
        select(Task)
        .options(
            selectinload(Task.tags),
            joinedload(Task.category),
            joinedload(Task.assignee),
        )
        .execution_options(populate_existing=True)
        .where(Task.id == task_id)
    )

    if user_id is not None:
        if allow_assigned:
            query = query.where(
                or_(
                    Task.user_id == user_id,
                    Task.assigned_to_id == user_id,
                )
            )
        else:
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
    category_id: int | None = None,
    category_name: str | None = None,
    tag_id: int | None = None,
    tag_name: str | None = None,
    assigned_to_id: int | None = None,
    view: str = "all",
    sort_by: str = "created_at",
    order: str = "desc",
) -> tuple[list[Task], int]:
    # Build shared filter conditions scoped to user
    filters = []
    if user_id is not None:
        if view == "created":
            filters.append(Task.user_id == user_id)
        elif view == "assigned":
            filters.append(Task.assigned_to_id == user_id)
        else:
            # "all" or default: user is either creator or assignee
            filters.append(
                or_(
                    Task.user_id == user_id,
                    Task.assigned_to_id == user_id,
                )
            )

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

    # Category filters
    if category_id is not None:
        filters.append(Task.category_id == category_id)
    if category_name and category_name.strip():
        filters.append(
            Task.category.has(func.lower(Category.name) == category_name.strip().lower())
        )

    # Tag filters
    if tag_id is not None:
        filters.append(Task.tags.any(Tag.id == tag_id))
    if tag_name and tag_name.strip():
        filters.append(
            Task.tags.any(func.lower(Tag.name) == tag_name.strip().lower())
        )

    # Assigned user filter
    if assigned_to_id is not None:
        filters.append(Task.assigned_to_id == assigned_to_id)

    # 1. Total count query with filters applied
    count_query = select(func.count(Task.id))
    if filters:
        count_query = count_query.where(*filters)

    count_result = await db.execute(count_query)
    total = count_result.scalar_one()

    # 2. Main data query with eager loading to prevent N+1 queries
    query = (
        select(Task)
        .options(
            selectinload(Task.tags),
            joinedload(Task.category),
            joinedload(Task.assignee),
        )
    )
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