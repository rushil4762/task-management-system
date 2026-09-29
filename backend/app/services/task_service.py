from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity import TaskActivity
from app.models.category import Category
from app.models.notification import NotificationType
from app.models.tag import Tag
from app.models.task import Task, TaskPriority, TaskStatus
from app.models.user import User
from app.repositories import (
    activity_repository,
    category_repository,
    tag_repository,
    task_repository,
    user_repository,
)
from app.schemas.activity import TaskActivityAction
from app.schemas.task import TaskCreate, TaskUpdate
from app.services import notification_service



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

    created_task = await task_repository.create_task(db, task)

    # Record task_created activity
    await activity_repository.create_activity(
        db,
        TaskActivity(
            task_id=created_task.id,
            user_id=user_id,
            action=TaskActivityAction.TASK_CREATED.value,
            description=f"Task '{created_task.title}' was created",
        ),
        commit=True,
    )

    # If assigned to another user, trigger task_assigned notification (never notify self)
    if created_task.assigned_to_id and created_task.assigned_to_id != user_id:
        await notification_service.create_notification(
            db=db,
            user_id=created_task.assigned_to_id,
            task_id=created_task.id,
            type=NotificationType.TASK_ASSIGNED,
            title=f"Task Assigned: {created_task.title}",
            message=f"You have been assigned to task '{created_task.title}'.",
            event_key=f"assigned_{created_task.id}_{created_task.assigned_to_id}",
        )

    # If created directly in completed status, trigger task_completed notification
    if created_task.status == TaskStatus.COMPLETED:
        await notification_service.create_notification(
            db=db,
            user_id=user_id,
            task_id=created_task.id,
            type=NotificationType.TASK_COMPLETED,
            title=f"Task Completed: {created_task.title}",
            message=f"Task '{created_task.title}' was marked as completed.",
            event_key=f"completed_{created_task.id}",
        )

    return created_task



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

    # Track pre-update state to record activities only on actual value changes
    old_title = task_entity.title
    old_description = task_entity.description
    old_status = task_entity.status
    old_priority = task_entity.priority
    old_category_id = task_entity.category_id
    old_assigned_to_id = task_entity.assigned_to_id
    old_tag_ids = {t.id for t in task_entity.tags}
    old_tags_by_id = {t.id: t.name for t in task_entity.tags}

    update_data = task_data.model_dump(
        exclude_unset=True,
    )
    activities_to_create: list[TaskActivity] = []

    # Validate category update
    if "category_id" in update_data:
        category = await _validate_and_get_category(db, update_data["category_id"], user_id)
        task_entity.category_id = update_data["category_id"]
        task_entity.category = category
        if update_data["category_id"] != old_category_id:
            desc = f"Category changed to '{category.name}'" if category is not None else "Category was removed"
            activities_to_create.append(
                TaskActivity(
                    task_id=task_entity.id,
                    user_id=user_id,
                    action=TaskActivityAction.CATEGORY_CHANGED.value,
                    description=desc,
                )
            )

    # Validate assignee update
    if "assigned_to_id" in update_data:
        assignee = await _validate_and_get_assignee(db, update_data["assigned_to_id"])
        task_entity.assigned_to_id = update_data["assigned_to_id"]
        task_entity.assignee = assignee
        if update_data["assigned_to_id"] != old_assigned_to_id:
            desc = f"Task was assigned to {assignee.name}" if assignee is not None else "Task was unassigned"
            activities_to_create.append(
                TaskActivity(
                    task_id=task_entity.id,
                    user_id=user_id,
                    action=TaskActivityAction.TASK_ASSIGNED.value,
                    description=desc,
                )
            )

    # Validate tags update
    if "tag_ids" in update_data:
        new_tags = await _validate_and_get_tags(db, update_data["tag_ids"], user_id)
        task_entity.tags = new_tags
        new_tag_ids = {t.id for t in new_tags}
        added_ids = new_tag_ids - old_tag_ids
        removed_ids = old_tag_ids - new_tag_ids
        for tag in new_tags:
            if tag.id in added_ids:
                activities_to_create.append(
                    TaskActivity(
                        task_id=task_entity.id,
                        user_id=user_id,
                        action=TaskActivityAction.TAG_ADDED.value,
                        description=f"Tag '{tag.name}' was added",
                    )
                )
        for tid in removed_ids:
            tname = old_tags_by_id.get(tid, str(tid))
            activities_to_create.append(
                TaskActivity(
                    task_id=task_entity.id,
                    user_id=user_id,
                    action=TaskActivityAction.TAG_REMOVED.value,
                    description=f"Tag '{tname}' was removed",
                )
            )

    # Automatic completion timestamp transitions based on status changes
    if "status" in update_data:
        new_status = update_data["status"]
        if new_status == TaskStatus.COMPLETED and task_entity.status != TaskStatus.COMPLETED:
            task_entity.completed_at = datetime.now(timezone.utc)
        elif new_status != TaskStatus.COMPLETED and task_entity.status == TaskStatus.COMPLETED:
            task_entity.completed_at = None

        if new_status != old_status:
            if new_status == TaskStatus.COMPLETED:
                activities_to_create.append(
                    TaskActivity(
                        task_id=task_entity.id,
                        user_id=user_id,
                        action=TaskActivityAction.TASK_COMPLETED.value,
                        description="Task was marked as completed",
                    )
                )
            elif old_status == TaskStatus.COMPLETED:
                activities_to_create.append(
                    TaskActivity(
                        task_id=task_entity.id,
                        user_id=user_id,
                        action=TaskActivityAction.TASK_REOPENED.value,
                        description=f"Task was reopened with status '{new_status.value}'",
                    )
                )
            else:
                activities_to_create.append(
                    TaskActivity(
                        task_id=task_entity.id,
                        user_id=user_id,
                        action=TaskActivityAction.STATUS_CHANGED.value,
                        description=f"Status changed from '{old_status.value}' to '{new_status.value}'",
                    )
                )

    # Priority change
    if "priority" in update_data and update_data["priority"] != old_priority:
        activities_to_create.append(
            TaskActivity(
                task_id=task_entity.id,
                user_id=user_id,
                action=TaskActivityAction.PRIORITY_CHANGED.value,
                description=f"Priority changed from '{old_priority.value}' to '{update_data['priority'].value}'",
            )
        )

    # Title / Description change
    title_changed = "title" in update_data and update_data["title"] != old_title
    desc_changed = "description" in update_data and update_data["description"] != old_description
    if title_changed or desc_changed:
        if title_changed and desc_changed:
            desc = "Task title and description were updated"
        elif title_changed:
            desc = f"Task title updated to '{update_data['title']}'"
        else:
            desc = "Task description was updated"
        activities_to_create.append(
            TaskActivity(
                task_id=task_entity.id,
                user_id=user_id,
                action=TaskActivityAction.TASK_UPDATED.value,
                description=desc,
            )
        )

    for field in ["title", "description", "status", "priority", "due_date"]:
        if field in update_data:
            setattr(task_entity, field, update_data[field])

    task_entity.updated_at = datetime.now(timezone.utc)

    updated_task = await task_repository.update_task(
        db,
        task_entity,
    )

    for act in activities_to_create:
        await activity_repository.create_activity(db, act, commit=True)

    # Deliver task_assigned notification on assignment change (skip self-assignment)
    if (
        old_assigned_to_id != updated_task.assigned_to_id
        and updated_task.assigned_to_id is not None
        and updated_task.assigned_to_id != user_id
    ):
        await notification_service.create_notification(
            db=db,
            user_id=updated_task.assigned_to_id,
            task_id=updated_task.id,
            type=NotificationType.TASK_ASSIGNED,
            title=f"Task Assigned: {updated_task.title}",
            message=f"You have been assigned to task '{updated_task.title}'.",
            event_key=f"assigned_{updated_task.id}_{updated_task.assigned_to_id}",
        )

    # Deliver task_completed notification on status transition to COMPLETED (avoid duplicates if already completed)
    if old_status != TaskStatus.COMPLETED and updated_task.status == TaskStatus.COMPLETED:
        await notification_service.create_notification(
            db=db,
            user_id=updated_task.user_id,
            task_id=updated_task.id,
            type=NotificationType.TASK_COMPLETED,
            title=f"Task Completed: {updated_task.title}",
            message=f"Task '{updated_task.title}' was marked as completed.",
            event_key=f"completed_{updated_task.id}",
        )
        if (
            updated_task.assigned_to_id is not None
            and updated_task.assigned_to_id != updated_task.user_id
            and updated_task.assigned_to_id != user_id
        ):
            await notification_service.create_notification(
                db=db,
                user_id=updated_task.assigned_to_id,
                task_id=updated_task.id,
                type=NotificationType.TASK_COMPLETED,
                title=f"Task Completed: {updated_task.title}",
                message=f"Task '{updated_task.title}' was marked as completed.",
                event_key=f"completed_{updated_task.id}",
            )

    return updated_task


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

    was_completed = task.status == TaskStatus.COMPLETED
    task.status = TaskStatus.COMPLETED
    task.completed_at = datetime.now(timezone.utc)
    task.updated_at = datetime.now(timezone.utc)

    updated = await task_repository.update_task(db, task)
    if not was_completed:
        await activity_repository.create_activity(
            db,
            TaskActivity(
                task_id=task.id,
                user_id=user_id,
                action=TaskActivityAction.TASK_COMPLETED.value,
                description="Task was marked as completed",
            ),
            commit=True,
        )
        # Notify task owner and assignee (avoid duplicate if already completed)
        await notification_service.create_notification(
            db=db,
            user_id=task.user_id,
            task_id=task.id,
            type=NotificationType.TASK_COMPLETED,
            title=f"Task Completed: {task.title}",
            message=f"Task '{task.title}' was marked as completed.",
            event_key=f"completed_{task.id}",
        )
        if (
            task.assigned_to_id is not None
            and task.assigned_to_id != task.user_id
            and task.assigned_to_id != user_id
        ):
            await notification_service.create_notification(
                db=db,
                user_id=task.assigned_to_id,
                task_id=task.id,
                type=NotificationType.TASK_COMPLETED,
                title=f"Task Completed: {task.title}",
                message=f"Task '{task.title}' was marked as completed.",
                event_key=f"completed_{task.id}",
            )
    return updated



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

    was_pending = task.status == TaskStatus.PENDING
    task.status = TaskStatus.PENDING
    task.completed_at = None
    task.updated_at = datetime.now(timezone.utc)

    updated = await task_repository.update_task(db, task)
    if not was_pending:
        await activity_repository.create_activity(
            db,
            TaskActivity(
                task_id=task.id,
                user_id=user_id,
                action=TaskActivityAction.TASK_REOPENED.value,
                description="Task was reopened",
            ),
            commit=True,
        )
    return updated


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
    added_tags = []
    for tag in tags:
        if tag.id not in existing_ids:
            task.tags.append(tag)
            added_tags.append(tag)

    task.updated_at = datetime.now(timezone.utc)
    updated = await task_repository.update_task(db, task)
    for tag in added_tags:
        await activity_repository.create_activity(
            db,
            TaskActivity(
                task_id=task.id,
                user_id=user_id,
                action=TaskActivityAction.TAG_ADDED.value,
                description=f"Tag '{tag.name}' was added",
            ),
            commit=True,
        )
    return updated


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

    removed_tag = next((t for t in task.tags if t.id == tag_id), None)
    if removed_tag is not None:
        task.tags = [t for t in task.tags if t.id != tag_id]
        task.updated_at = datetime.now(timezone.utc)
        updated = await task_repository.update_task(db, task)
        await activity_repository.create_activity(
            db,
            TaskActivity(
                task_id=task.id,
                user_id=user_id,
                action=TaskActivityAction.TAG_REMOVED.value,
                description=f"Tag '{removed_tag.name}' was removed",
            ),
            commit=True,
        )
        return updated

    return task


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