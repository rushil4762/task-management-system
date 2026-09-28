from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.models.tag import Tag
from app.models.task import Task, TaskPriority, TaskStatus
from app.models.user import User
from app.repositories import (
    category_repository,
    tag_repository,
    task_repository,
    user_repository,
)
from app.schemas.task import TaskCreate, TaskUpdate


async def _validate_and_get_category(
    db: AsyncSession,
    category_id: int | None,
    user_id: int,
) -> Category | None:
    if category_id is not None:
        cat = await category_repository.get_category_by_id(
            db=db,
            category_id=category_id,
            user_id=user_id,
        )
        if cat is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category not found or does not belong to the user",
            )
        return cat
    return None


async def _validate_and_get_assignee(
    db: AsyncSession,
    assigned_to_id: int | None,
) -> User | None:
    if assigned_to_id is not None:
        user = await user_repository.get_user_by_id(
            db=db,
            user_id=assigned_to_id,
        )
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot assign task: assigned user does not exist",
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot assign task: assigned user is inactive",
            )
        return user
    return None


async def _validate_and_get_tags(
    db: AsyncSession,
    tag_ids: list[int] | None,
    user_id: int,
) -> list[Tag]:
    if not tag_ids:
        return []
    unique_tag_ids = list(dict.fromkeys(tag_ids))
    tags = await tag_repository.get_tags_by_ids(
        db=db,
        tag_ids=unique_tag_ids,
        user_id=user_id,
    )
    if len(tags) != len(unique_tag_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or more tags do not exist or do not belong to the user",
        )
    return tags


async def create_task(
    db: AsyncSession,
    user_id: int,
    task_data: TaskCreate,
) -> Task:
    # 1. Validate category ownership if specified
    category = await _validate_and_get_category(db, task_data.category_id, user_id)

    # 2. Validate assignee user validity and active status if specified
    assignee = await _validate_and_get_assignee(db, task_data.assigned_to_id)

    # 3. Validate tag ownership if tags specified
    tags = await _validate_and_get_tags(db, task_data.tag_ids, user_id)

    completed_at = (
        datetime.now(timezone.utc)
        if task_data.status == TaskStatus.COMPLETED
        else None
    )

    task = Task(
        title=task_data.title,
        description=task_data.description,
        status=task_data.status,
        priority=task_data.priority,
        due_date=task_data.due_date,
        completed_at=completed_at,
        user_id=user_id,
        category_id=task_data.category_id,
        assigned_to_id=task_data.assigned_to_id,
    )
    if category is not None:
        task.category = category
    if assignee is not None:
        task.assignee = assignee
    if tags:
        task.tags = tags

    return await task_repository.create_task(db, task)



async def get_task(
    db: AsyncSession,
    task_id: int,
    user_id: int,
) -> Task | None:
    # Allows viewing if user is owner OR assignee
    return await task_repository.get_task_by_id(
        db=db,
        task_id=task_id,
        user_id=user_id,
        allow_assigned=True,
    )


async def get_tasks(
    db: AsyncSession,
    user_id: int,
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
    return await task_repository.get_tasks(
        db=db,
        user_id=user_id,
        limit=limit,
        offset=offset,
        search=search,
        status=status,
        priority=priority,
        due_date_from=due_date_from,
        due_date_to=due_date_to,
        is_overdue=is_overdue,
        is_completed=is_completed,
        category_id=category_id,
        category_name=category_name,
        tag_id=tag_id,
        tag_name=tag_name,
        assigned_to_id=assigned_to_id,
        view=view,
        sort_by=sort_by,
        order=order,
    )


async def update_task(
    db: AsyncSession,
    task: Task | int,
    user_id: int,
    task_data: TaskUpdate,
) -> Task | None:
    task_entity: Task | None
    if isinstance(task, int):
        task_entity = await task_repository.get_task_by_id(
            db=db,
            task_id=task,
        )
        if task_entity is None:
            return None
    else:
        task_entity = task

    # Enforce strict ownership: assignees cannot modify tasks
    if task_entity.user_id != user_id:
        if task_entity.assigned_to_id == user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to modify this task: only the task owner can modify tasks",
            )
        return None

    update_data = task_data.model_dump(
        exclude_unset=True,
    )

    # Validate category update
    if "category_id" in update_data:
        category = await _validate_and_get_category(db, update_data["category_id"], user_id)
        task_entity.category_id = update_data["category_id"]
        task_entity.category = category

    # Validate assignee update
    if "assigned_to_id" in update_data:
        assignee = await _validate_and_get_assignee(db, update_data["assigned_to_id"])
        task_entity.assigned_to_id = update_data["assigned_to_id"]
        task_entity.assignee = assignee

    # Validate tags update
    if "tag_ids" in update_data:
        new_tags = await _validate_and_get_tags(db, update_data["tag_ids"], user_id)
        task_entity.tags = new_tags

    # Automatic completion timestamp transitions based on status changes
    if "status" in update_data:
        new_status = update_data["status"]
        if new_status == TaskStatus.COMPLETED and task_entity.status != TaskStatus.COMPLETED:
            task_entity.completed_at = datetime.now(timezone.utc)
        elif new_status != TaskStatus.COMPLETED and task_entity.status == TaskStatus.COMPLETED:
            task_entity.completed_at = None

    for field in ["title", "description", "status", "priority", "due_date"]:
        if field in update_data:
            setattr(task_entity, field, update_data[field])

    task_entity.updated_at = datetime.now(timezone.utc)

    return await task_repository.update_task(
        db,
        task_entity,
    )


async def mark_task_completed(
    db: AsyncSession,
    task_id: int,
    user_id: int,
) -> Task | None:
    task = await task_repository.get_task_by_id(
        db=db,
        task_id=task_id,
    )
    if task is None:
        return None

    if task.user_id != user_id:
        if task.assigned_to_id == user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized: only the task owner can complete tasks",
            )
        return None

    task.status = TaskStatus.COMPLETED
    task.completed_at = datetime.now(timezone.utc)
    task.updated_at = datetime.now(timezone.utc)

    return await task_repository.update_task(db, task)


async def reopen_task(
    db: AsyncSession,
    task_id: int,
    user_id: int,
) -> Task | None:
    task = await task_repository.get_task_by_id(
        db=db,
        task_id=task_id,
    )
    if task is None:
        return None

    if task.user_id != user_id:
        if task.assigned_to_id == user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized: only the task owner can reopen tasks",
            )
        return None

    task.status = TaskStatus.PENDING
    task.completed_at = None
    task.updated_at = datetime.now(timezone.utc)

    return await task_repository.update_task(db, task)


async def delete_task(
    db: AsyncSession,
    task: Task | int,
    user_id: int,
) -> bool:
    task_entity: Task | None
    if isinstance(task, int):
        task_entity = await task_repository.get_task_by_id(
            db=db,
            task_id=task,
        )
        if task_entity is None:
            return False
    else:
        task_entity = task

    if task_entity.user_id != user_id:
        if task_entity.assigned_to_id == user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized: only the task owner can delete tasks",
            )
        return False

    await task_repository.delete_task(
        db,
        task_entity,
    )
    return True


async def attach_tags_to_task(
    db: AsyncSession,
    task_id: int,
    tag_ids: list[int],
    user_id: int,
) -> Task:
    task = await task_repository.get_task_by_id(db, task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    if task.user_id != user_id:
        if task.assigned_to_id == user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized: only the task owner can attach tags to tasks",
            )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    tags = await _validate_and_get_tags(db, tag_ids, user_id)
    existing_ids = {t.id for t in task.tags}
    for tag in tags:
        if tag.id not in existing_ids:
            task.tags.append(tag)

    task.updated_at = datetime.now(timezone.utc)
    return await task_repository.update_task(db, task)


async def remove_tag_from_task(
    db: AsyncSession,
    task_id: int,
    tag_id: int,
    user_id: int,
) -> Task:
    task = await task_repository.get_task_by_id(db, task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    if task.user_id != user_id:
        if task.assigned_to_id == user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized: only the task owner can remove tags from tasks",
            )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    task.tags = [t for t in task.tags if t.id != tag_id]
    task.updated_at = datetime.now(timezone.utc)
    return await task_repository.update_task(db, task)


async def bulk_delete_tasks(
    db: AsyncSession,
    task_ids: list[int],
    user_id: int,
) -> int:
    if not task_ids:
        return 0
    return await task_repository.delete_tasks_bulk(
        db=db,
        task_ids=task_ids,
        user_id=user_id,
    )