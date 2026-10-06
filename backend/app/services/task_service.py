from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity import TaskActivity
from app.models.category import Category
from app.models.notification import NotificationType
from app.models.tag import Tag
from app.models.task import Task, TaskPriority, TaskStatus
from app.models.user import User, UserRole
from app.repositories import (
    activity_repository,
    category_repository,
    tag_repository,
    task_repository,
    user_repository,
)
from app.schemas.activity import TaskActivityAction
from app.schemas.task import TaskCreate, TaskUpdate
from app.services import activity_service, notification_service



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
    role: UserRole = UserRole.CEO,
) -> Task:
    if role == UserRole.EMPLOYEE and task_data.assigned_to_id is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only CEO can assign tasks",
        )

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
    actor = await user_repository.get_user_by_id(db, user_id)
    actor_name = actor.name if actor else "User"
    await activity_repository.create_activity(
        db,
        TaskActivity(
            task_id=created_task.id,
            user_id=user_id,
            action=TaskActivityAction.TASK_CREATED.value,
            description=f"{actor_name} created this task",
            meta_data={"title": created_task.title},
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
    role: UserRole = UserRole.CEO,
) -> Task | None:
    if role == UserRole.EMPLOYEE:
        task = await task_repository.get_task_by_id(
            db=db,
            task_id=task_id,
        )
        if task is None:
            return None
        if task.assigned_to_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: You cannot access tasks not assigned to you",
            )
        return task

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
    role: UserRole = UserRole.CEO,
) -> tuple[list[Task], int]:
    target_view = view
    target_assigned_to = assigned_to_id
    if role == UserRole.EMPLOYEE:
        target_view = "assigned"
        target_assigned_to = user_id

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
        assigned_to_id=target_assigned_to,
        view=target_view,
        sort_by=sort_by,
        order=order,
    )


async def update_task(
    db: AsyncSession,
    task: Task | int,
    user_id: int,
    task_data: TaskUpdate,
    role: UserRole = UserRole.CEO,
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

    if role == UserRole.EMPLOYEE:
        if task_entity.assigned_to_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: You can only update tasks assigned to you",
            )
        update_dict = task_data.model_dump(exclude_unset=True)
        if "assigned_to_id" in update_dict:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only CEO can assign tasks",
            )
        restricted_keys = set(update_dict.keys()) - {"status"}
        if restricted_keys:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Employees are only permitted to update task status",
            )
        if "status" in update_dict:
            new_status = update_dict["status"]
            old_status = task_entity.status
            task_entity.status = new_status
            if new_status == TaskStatus.COMPLETED and old_status != TaskStatus.COMPLETED:
                task_entity.completed_at = datetime.now(timezone.utc)
            elif new_status != TaskStatus.COMPLETED and old_status == TaskStatus.COMPLETED:
                task_entity.completed_at = None
            task_entity.updated_at = datetime.now(timezone.utc)
            updated_task = await task_repository.update_task(db, task_entity)
            if new_status != old_status:
                actor = await user_repository.get_user_by_id(db, user_id)
                actor_name = actor.name if actor else "User"
                if new_status == TaskStatus.COMPLETED:
                    act_action = TaskActivityAction.TASK_COMPLETED.value
                    desc = f"{actor_name} completed the task"
                elif old_status == TaskStatus.COMPLETED:
                    act_action = TaskActivityAction.TASK_REOPENED.value
                    desc = f"{actor_name} reopened the task"
                else:
                    act_action = TaskActivityAction.STATUS_CHANGED.value
                    desc = activity_service.build_status_message(actor_name, old_status, new_status)

                await activity_repository.create_activity(
                    db,
                    TaskActivity(
                        task_id=task_entity.id,
                        user_id=user_id,
                        action=act_action,
                        description=desc,
                        meta_data={"old_value": old_status.value, "new_value": new_status.value},
                    ),
                    commit=True,
                )
                if old_status != TaskStatus.COMPLETED and new_status == TaskStatus.COMPLETED:
                    await notification_service.create_notification(
                        db=db,
                        user_id=task_entity.user_id,
                        task_id=task_entity.id,
                        type=NotificationType.TASK_COMPLETED,
                        title=f"Task Completed: {task_entity.title}",
                        message=f"Task '{task_entity.title}' was marked as completed.",
                        event_key=f"completed_{task_entity.id}",
                    )
            return updated_task
        return task_entity

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

    old_due_date = task_entity.due_date

    update_data = task_data.model_dump(
        exclude_unset=True,
    )
    activities_to_create: list[TaskActivity] = []

    actor = await user_repository.get_user_by_id(db, user_id)
    actor_name = actor.name if actor else "User"

    # Validate category update
    if "category_id" in update_data:
        category = await _validate_and_get_category(db, update_data["category_id"], user_id)
        old_category_name = task_entity.category.name if task_entity.category else None
        task_entity.category_id = update_data["category_id"]
        task_entity.category = category
        if update_data["category_id"] != old_category_id:
            new_category_name = category.name if category is not None else None
            desc = activity_service.build_category_message(actor_name, old_category_name, new_category_name)
            meta = {
                "old_category_id": old_category_id,
                "old_category_name": old_category_name,
                "new_category_id": update_data["category_id"],
                "new_category_name": new_category_name,
                "old_value": old_category_name,
                "new_value": new_category_name,
            }
            activities_to_create.append(
                TaskActivity(
                    task_id=task_entity.id,
                    user_id=user_id,
                    action=TaskActivityAction.CATEGORY_CHANGED.value,
                    description=desc,
                    meta_data=meta,
                )
            )

    # Validate assignee update
    if "assigned_to_id" in update_data:
        assignee = await _validate_and_get_assignee(db, update_data["assigned_to_id"])
        old_assignee_name = task_entity.assignee.name if task_entity.assignee else None
        task_entity.assigned_to_id = update_data["assigned_to_id"]
        task_entity.assignee = assignee
        if update_data["assigned_to_id"] != old_assigned_to_id:
            new_assignee_name = assignee.name if assignee is not None else None
            desc = activity_service.build_assignment_message(actor_name, new_assignee_name)
            meta = {
                "old_assignee_id": old_assigned_to_id,
                "old_assignee_name": old_assignee_name,
                "new_assignee_id": update_data["assigned_to_id"],
                "new_assignee_name": new_assignee_name,
            }
            activities_to_create.append(
                TaskActivity(
                    task_id=task_entity.id,
                    user_id=user_id,
                    action=TaskActivityAction.TASK_ASSIGNED.value,
                    description=desc,
                    meta_data=meta,
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
                        description=f"{actor_name} added tag {tag.name}",
                        meta_data={"tag_id": tag.id, "tag_name": tag.name},
                    )
                )
        for tid in removed_ids:
            tname = old_tags_by_id.get(tid, str(tid))
            activities_to_create.append(
                TaskActivity(
                    task_id=task_entity.id,
                    user_id=user_id,
                    action=TaskActivityAction.TAG_REMOVED.value,
                    description=f"{actor_name} removed tag {tname}",
                    meta_data={"tag_id": tid, "tag_name": tname},
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
                        description=f"{actor_name} completed the task",
                        meta_data={"old_value": old_status.value, "new_value": new_status.value},
                    )
                )
            elif old_status == TaskStatus.COMPLETED:
                activities_to_create.append(
                    TaskActivity(
                        task_id=task_entity.id,
                        user_id=user_id,
                        action=TaskActivityAction.TASK_REOPENED.value,
                        description=f"{actor_name} reopened the task",
                        meta_data={"old_value": old_status.value, "new_value": new_status.value},
                    )
                )
            else:
                activities_to_create.append(
                    TaskActivity(
                        task_id=task_entity.id,
                        user_id=user_id,
                        action=TaskActivityAction.STATUS_CHANGED.value,
                        description=activity_service.build_status_message(actor_name, old_status, new_status),
                        meta_data={"old_value": old_status.value, "new_value": new_status.value},
                    )
                )

    # Priority change
    if "priority" in update_data and update_data["priority"] != old_priority:
        activities_to_create.append(
            TaskActivity(
                task_id=task_entity.id,
                user_id=user_id,
                action=TaskActivityAction.PRIORITY_CHANGED.value,
                description=activity_service.build_priority_message(actor_name, old_priority, update_data["priority"]),
                meta_data={"old_value": old_priority.value, "new_value": update_data["priority"].value},
            )
        )

    # Due date change
    if "due_date" in update_data and not activity_service.are_datetimes_equal(old_due_date, update_data["due_date"]):
        activities_to_create.append(
            TaskActivity(
                task_id=task_entity.id,
                user_id=user_id,
                action=TaskActivityAction.DUE_DATE_CHANGED.value,
                description=activity_service.build_due_date_message(actor_name, old_due_date, update_data["due_date"]),
                meta_data={
                    "old_value": old_due_date.isoformat() if old_due_date else None,
                    "new_value": update_data["due_date"].isoformat() if update_data["due_date"] else None,
                },
            )
        )

    # Title / Description change
    title_changed = "title" in update_data and update_data["title"] != old_title
    desc_changed = "description" in update_data and update_data["description"] != old_description
    if title_changed or desc_changed:
        fields = []
        if title_changed:
            fields.append("title")
        if desc_changed:
            fields.append("description")

        if title_changed and desc_changed:
            desc = f"{actor_name} updated task title and description"
        elif title_changed:
            desc = f"{actor_name} updated task title to '{update_data['title']}'"
        else:
            desc = f"{actor_name} updated task description"

        activities_to_create.append(
            TaskActivity(
                task_id=task_entity.id,
                user_id=user_id,
                action=TaskActivityAction.TASK_UPDATED.value,
                description=desc,
                meta_data={"fields_updated": fields, "old_title": old_title, "new_title": update_data.get("title", old_title)},
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


async def assign_task(
    db: AsyncSession,
    task_id: int,
    user_id: int,
    assigned_to_id: int | None,
    role: UserRole = UserRole.CEO,
) -> Task:
    if role != UserRole.CEO:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only CEO can assign tasks",
        )

    task = await task_repository.get_task_by_id(db=db, task_id=task_id)
    if task is None or task.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    old_assigned_to_id = task.assigned_to_id
    if old_assigned_to_id == assigned_to_id:
        return task

    old_assignee_name = task.assignee.name if task.assignee else None
    assignee = await _validate_and_get_assignee(db, assigned_to_id)
    task.assigned_to_id = assigned_to_id
    task.assignee = assignee
    task.updated_at = datetime.now(timezone.utc)

    updated_task = await task_repository.update_task(db, task)
    actor = await user_repository.get_user_by_id(db, user_id)
    actor_name = actor.name if actor else "User"
    new_assignee_name = assignee.name if assignee is not None else None
    desc = activity_service.build_assignment_message(actor_name, new_assignee_name)
    meta = {
        "old_assignee_id": old_assigned_to_id,
        "old_assignee_name": old_assignee_name,
        "new_assignee_id": assigned_to_id,
        "new_assignee_name": new_assignee_name,
    }
    await activity_repository.create_activity(
        db,
        TaskActivity(
            task_id=task.id,
            user_id=user_id,
            action=TaskActivityAction.TASK_ASSIGNED.value,
            description=desc,
            meta_data=meta,
        ),
        commit=True,
    )

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

    return updated_task


async def mark_task_completed(
    db: AsyncSession,
    task_id: int,
    user_id: int,
    role: UserRole = UserRole.CEO,
) -> Task | None:
    task = await task_repository.get_task_by_id(
        db=db,
        task_id=task_id,
    )
    if task is None:
        return None

    if role == UserRole.EMPLOYEE:
        if task.assigned_to_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: You can only complete tasks assigned to you",
            )
    else:
        if task.user_id != user_id:
            if task.assigned_to_id == user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized: only the task owner can complete tasks",
                )
            return None

    was_completed = task.status == TaskStatus.COMPLETED
    old_status_val = task.status.value
    task.status = TaskStatus.COMPLETED
    task.completed_at = datetime.now(timezone.utc)
    task.updated_at = datetime.now(timezone.utc)

    updated = await task_repository.update_task(db, task)
    if not was_completed:
        actor = await user_repository.get_user_by_id(db, user_id)
        actor_name = actor.name if actor else "User"
        await activity_repository.create_activity(
            db,
            TaskActivity(
                task_id=task.id,
                user_id=user_id,
                action=TaskActivityAction.TASK_COMPLETED.value,
                description=f"{actor_name} completed the task",
                meta_data={"old_value": old_status_val, "new_value": "completed"},
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
    role: UserRole = UserRole.CEO,
) -> Task | None:
    task = await task_repository.get_task_by_id(
        db=db,
        task_id=task_id,
    )
    if task is None:
        return None

    if role == UserRole.EMPLOYEE:
        if task.assigned_to_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: You can only reopen tasks assigned to you",
            )
    else:
        if task.user_id != user_id:
            if task.assigned_to_id == user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized: only the task owner can reopen tasks",
                )
            return None

    was_pending = task.status == TaskStatus.PENDING
    old_status_val = task.status.value
    task.status = TaskStatus.PENDING
    task.completed_at = None
    task.updated_at = datetime.now(timezone.utc)

    updated = await task_repository.update_task(db, task)
    if not was_pending:
        actor = await user_repository.get_user_by_id(db, user_id)
        actor_name = actor.name if actor else "User"
        await activity_repository.create_activity(
            db,
            TaskActivity(
                task_id=task.id,
                user_id=user_id,
                action=TaskActivityAction.TASK_REOPENED.value,
                description=f"{actor_name} reopened the task",
                meta_data={"old_value": old_status_val, "new_value": "pending"},
            ),
            commit=True,
        )
    return updated


async def delete_task(
    db: AsyncSession,
    task: Task | int,
    user_id: int,
    role: UserRole = UserRole.CEO,
) -> bool:
    if role == UserRole.EMPLOYEE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Employees cannot delete tasks",
        )

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
    role: UserRole = UserRole.CEO,
) -> Task:
    if role == UserRole.EMPLOYEE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Employees cannot modify task tags",
        )

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
    if added_tags:
        actor = await user_repository.get_user_by_id(db, user_id)
        actor_name = actor.name if actor else "User"
        for tag in added_tags:
            await activity_repository.create_activity(
                db,
                TaskActivity(
                    task_id=task.id,
                    user_id=user_id,
                    action=TaskActivityAction.TAG_ADDED.value,
                    description=f"{actor_name} added tag {tag.name}",
                    meta_data={"tag_id": tag.id, "tag_name": tag.name},
                ),
                commit=True,
            )
    return updated


async def remove_tag_from_task(
    db: AsyncSession,
    task_id: int,
    tag_id: int,
    user_id: int,
    role: UserRole = UserRole.CEO,
) -> Task:
    if role == UserRole.EMPLOYEE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Employees cannot modify task tags",
        )

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
        actor = await user_repository.get_user_by_id(db, user_id)
        actor_name = actor.name if actor else "User"
        task.tags = [t for t in task.tags if t.id != tag_id]
        task.updated_at = datetime.now(timezone.utc)
        updated = await task_repository.update_task(db, task)
        await activity_repository.create_activity(
            db,
            TaskActivity(
                task_id=task.id,
                user_id=user_id,
                action=TaskActivityAction.TAG_REMOVED.value,
                description=f"{actor_name} removed tag {removed_tag.name}",
                meta_data={"tag_id": removed_tag.id, "tag_name": removed_tag.name},
            ),
            commit=True,
        )
        return updated

    return task


async def bulk_delete_tasks(
    db: AsyncSession,
    task_ids: list[int],
    user_id: int,
    role: UserRole = UserRole.CEO,
) -> int:
    if role == UserRole.EMPLOYEE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Employees cannot delete tasks",
        )

    if not task_ids:
        return 0
    return await task_repository.delete_tasks_bulk(
        db=db,
        task_ids=task_ids,
        user_id=user_id,
    )