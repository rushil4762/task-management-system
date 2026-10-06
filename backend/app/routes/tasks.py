from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.task import TaskPriority, TaskStatus
from app.models.user import User, UserRole
from app.schemas.tag import TaskTagsAttachRequest
from app.schemas.task import (
    BulkDeleteRequest,
    BulkDeleteResponse,
    SortOrder,
    TaskAssignRequest,
    TaskCreate,
    TaskListResponse,
    TaskResponse,
    TaskSortBy,
    TaskUpdate,
)
from app.services import task_service

router = APIRouter(
    prefix="/tasks",
    tags=["Tasks"],
)


@router.post(
    "",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task for the authenticated user",
)
async def create_task(
    task_data: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await task_service.create_task(
        db=db,
        user_id=current_user.id,
        task_data=task_data,
        role=current_user.role,
    )


@router.get(
    "",
    response_model=TaskListResponse,
    summary="List tasks with search, advanced filtering, sorting, and pagination",
)
async def get_tasks(
    limit: int = Query(
        default=10,
        ge=1,
        le=100,
        description="Maximum number of tasks to return (1-100)",
    ),
    offset: int = Query(
        default=0,
        ge=0,
        description="Number of tasks to skip",
    ),
    search: str | None = Query(
        default=None,
        description="Search keyword matching title or description (case-insensitive)",
    ),
    status_filter: TaskStatus | None = Query(
        default=None,
        alias="status",
        description="Filter by task status (pending, in_progress, completed, cancelled)",
    ),
    priority_filter: TaskPriority | None = Query(
        default=None,
        alias="priority",
        description="Filter by task priority (low, medium, high, urgent)",
    ),
    due_date_from: datetime | None = Query(
        default=None,
        description="Filter tasks due on or after this timestamp",
    ),
    due_date_to: datetime | None = Query(
        default=None,
        description="Filter tasks due on or before this timestamp",
    ),
    is_overdue: bool | None = Query(
        default=None,
        description="Filter overdue tasks (past due date and not completed/cancelled)",
    ),
    is_completed: bool | None = Query(
        default=None,
        description="Filter completed (true) or non-completed (false) tasks",
    ),
    category_id: int | None = Query(
        default=None,
        description="Filter tasks by category ID",
    ),
    category: str | None = Query(
        default=None,
        description="Filter tasks by category name (case-insensitive)",
    ),
    tag_id: int | None = Query(
        default=None,
        description="Filter tasks by tag ID",
    ),
    tag: str | None = Query(
        default=None,
        description="Filter tasks by tag name (case-insensitive)",
    ),
    assigned_to_id: int | None = Query(
        default=None,
        alias="assigned_to_id",
        description="Filter tasks by assigned user ID",
    ),
    assigned_user: int | None = Query(
        default=None,
        alias="assigned_user",
        description="Filter tasks by assigned user ID (alias)",
    ),
    view: str = Query(
        default="all",
        description="Task view: 'created' (tasks created by user), 'assigned' (tasks assigned to user), or 'all' (created or assigned)",
    ),
    sort_by: TaskSortBy = Query(
        default=TaskSortBy.CREATED_AT,
        description="Field to sort tasks by",
    ),
    order: SortOrder = Query(
        default=SortOrder.DESC,
        description="Sort direction (asc or desc)",
    ),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    target_assigned_to = assigned_to_id if assigned_to_id is not None else assigned_user

    tasks, total = await task_service.get_tasks(
        db=db,
        user_id=current_user.id,
        limit=limit,
        offset=offset,
        search=search,
        status=status_filter,
        priority=priority_filter,
        due_date_from=due_date_from,
        due_date_to=due_date_to,
        is_overdue=is_overdue,
        is_completed=is_completed,
        category_id=category_id,
        category_name=category,
        tag_id=tag_id,
        tag_name=tag,
        assigned_to_id=target_assigned_to,
        view=view,
        sort_by=sort_by.value,
        order=order.value,
        role=current_user.role,
    )

    return {
        "items": tasks,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.post(
    "/bulk-delete",
    response_model=BulkDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Bulk delete multiple tasks (CEO only)",
)
async def bulk_delete_tasks(
    bulk_data: BulkDeleteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    deleted_count = await task_service.bulk_delete_tasks(
        db=db,
        task_ids=bulk_data.task_ids,
        user_id=current_user.id,
        role=current_user.role,
    )

    return {
        "deleted_count": deleted_count,
        "message": f"Successfully deleted {deleted_count} task(s)",
    }


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Get a task by ID (creator or assigned employee)",
)
async def get_task(
    task_id: int = Path(..., ge=1, description="Unique integer ID of the task"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = await task_service.get_task(
        db=db,
        task_id=task_id,
        user_id=current_user.id,
        role=current_user.role,
    )

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    return task


@router.patch(
    "/{task_id}/assign",
    response_model=TaskResponse,
    summary="Assign a task to an employee (CEO only)",
)
@router.post(
    "/{task_id}/assign",
    response_model=TaskResponse,
    summary="Assign a task to an employee (alternative method, CEO only)",
)
async def assign_task(
    assign_data: TaskAssignRequest,
    task_id: int = Path(..., ge=1, description="Unique integer ID of the task"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await task_service.assign_task(
        db=db,
        task_id=task_id,
        user_id=current_user.id,
        assigned_to_id=assign_data.assigned_to_id,
        role=current_user.role,
    )


@router.put(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Update a task by ID (CEO for full edit, Employee for status)",
)
@router.patch(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Partially update a task by ID",
)
async def update_task(
    task_data: TaskUpdate,
    task_id: int = Path(..., ge=1, description="Unique integer ID of the task"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    updated_task = await task_service.update_task(
        db=db,
        task=task_id,
        user_id=current_user.id,
        task_data=task_data,
        role=current_user.role,
    )

    if updated_task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    return updated_task


@router.patch(
    "/{task_id}/complete",
    response_model=TaskResponse,
    summary="Mark a task as completed",
)
@router.post(
    "/{task_id}/complete",
    response_model=TaskResponse,
    summary="Mark a task as completed (alternative method)",
)
async def mark_task_completed(
    task_id: int = Path(..., ge=1, description="Unique integer ID of the task"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = await task_service.mark_task_completed(
        db=db,
        task_id=task_id,
        user_id=current_user.id,
        role=current_user.role,
    )

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    return task


@router.patch(
    "/{task_id}/reopen",
    response_model=TaskResponse,
    summary="Reopen a completed task",
)
@router.post(
    "/{task_id}/reopen",
    response_model=TaskResponse,
    summary="Reopen a completed task (alternative method)",
)
async def reopen_task(
    task_id: int = Path(..., ge=1, description="Unique integer ID of the task"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = await task_service.reopen_task(
        db=db,
        task_id=task_id,
        user_id=current_user.id,
        role=current_user.role,
    )

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    return task


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a task by ID (CEO only)",
)
async def delete_task(
    task_id: int = Path(..., ge=1, description="Unique integer ID of the task"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    deleted = await task_service.delete_task(
        db=db,
        task=task_id,
        user_id=current_user.id,
        role=current_user.role,
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )


@router.post(
    "/{task_id}/tags",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Attach tags to a task (CEO only)",
)
async def attach_tags_to_task(
    attach_data: TaskTagsAttachRequest,
    task_id: int = Path(..., ge=1, description="Unique integer ID of the task"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await task_service.attach_tags_to_task(
        db=db,
        task_id=task_id,
        tag_ids=attach_data.tag_ids,
        user_id=current_user.id,
        role=current_user.role,
    )


@router.delete(
    "/{task_id}/tags/{tag_id}",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Remove a tag from a task (CEO only)",
)
async def remove_tag_from_task(
    task_id: int = Path(..., ge=1, description="Unique integer ID of the task"),
    tag_id: int = Path(..., ge=1, description="Unique integer ID of the tag to detach"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await task_service.remove_tag_from_task(
        db=db,
        task_id=task_id,
        tag_id=tag_id,
        user_id=current_user.id,
        role=current_user.role,
    )