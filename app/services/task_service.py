from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task, TaskPriority, TaskStatus
from app.repositories import task_repository
from app.schemas.task import TaskCreate, TaskUpdate


async def create_task(
    db: AsyncSession,
    task_data: TaskCreate,
) -> Task:
    task = Task(
        title=task_data.title,
        description=task_data.description,
        status=task_data.status,
        priority=task_data.priority,
    )
    return await task_repository.create_task(db, task)


async def get_task(
    db: AsyncSession,
    task_id: int,
) -> Task | None:
    return await task_repository.get_task_by_id(
        db,
        task_id,
    )


async def get_tasks(
    db: AsyncSession,
    limit: int = 10,
    offset: int = 0,
    status: TaskStatus | None = None,
    priority: TaskPriority | None = None,
    sort_by: str = "created_at",
    order: str = "desc",
) -> tuple[list[Task], int]:
    return await task_repository.get_tasks(
        db=db,
        limit=limit,
        offset=offset,
        status=status,
        priority=priority,
        sort_by=sort_by,
        order=order,
    )


async def update_task(
    db: AsyncSession,
    task: Task | int,
    task_data: TaskUpdate,
) -> Task | None:
    task_entity: Task | None
    if isinstance(task, int):
        task_entity = await task_repository.get_task_by_id(db, task)
        if task_entity is None:
            return None
    else:
        task_entity = task

    update_data = task_data.model_dump(
        exclude_unset=True,
    )

    for field, value in update_data.items():
        setattr(task_entity, field, value)

    task_entity.updated_at = datetime.now(timezone.utc)

    return await task_repository.update_task(
        db,
        task_entity,
    )


async def delete_task(
    db: AsyncSession,
    task: Task | int,
) -> bool:
    task_entity: Task | None
    if isinstance(task, int):
        task_entity = await task_repository.get_task_by_id(db, task)
        if task_entity is None:
            return False
    else:
        task_entity = task

    await task_repository.delete_task(
        db,
        task_entity,
    )
    return True