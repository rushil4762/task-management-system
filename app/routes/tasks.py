from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.task import TaskPriority, TaskStatus
from app.models.user import User
from app.schemas.task import (
    BulkDeleteRequest,
    BulkDeleteResponse,
    SortOrder,
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
        sort_by=sort_by.value,
        order=order.value,
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
    summary="Bulk delete multiple tasks owned by the authenticated user",
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
    )

    return {
        "deleted_count": deleted_count,
        "message": f"Successfully deleted {deleted_count} task(s)",
    }


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Get an owned task by ID",
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
    )

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    return task


@router.put(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Update an owned task by ID",
)
@router.patch(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Partially update an owned task by ID",
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
    summary="Mark an owned task as completed",
)
@router.post(
    "/{task_id}/complete",
    response_model=TaskResponse,
    summary="Mark an owned task as completed (alternative method)",
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
    summary="Delete an owned task by ID",
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
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )