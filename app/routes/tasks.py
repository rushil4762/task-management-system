from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.task import TaskPriority, TaskStatus
from app.schemas.task import (
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
    summary="Create a new task",
)
async def create_task(
    task_data: TaskCreate,
    db: AsyncSession = Depends(get_db),
):
    return await task_service.create_task(
        db=db,
        task_data=task_data,
    )


@router.get(
    "",
    response_model=TaskListResponse,
    summary="List tasks with filtering, sorting, and pagination",
)
async def get_tasks(
    limit: int = Query(
        default=10,
        ge=1,
        le=100,
        description="Maximum number of tasks to return",
    ),
    offset: int = Query(
        default=0,
        ge=0,
        description="Number of tasks to skip",
    ),
    status_filter: TaskStatus | None = Query(
        default=None,
        alias="status",
        description="Filter by task status",
    ),
    priority_filter: TaskPriority | None = Query(
        default=None,
        alias="priority",
        description="Filter by task priority",
    ),
    sort_by: TaskSortBy = Query(
        default=TaskSortBy.CREATED_AT,
        description="Field to sort tasks by",
    ),
    order: SortOrder = Query(
        default=SortOrder.DESC,
        description="Sort direction (asc or desc)",
    ),
    db: AsyncSession = Depends(get_db),
):
    tasks, total = await task_service.get_tasks(
        db=db,
        limit=limit,
        offset=offset,
        status=status_filter,
        priority=priority_filter,
        sort_by=sort_by.value,
        order=order.value,
    )

    return {
        "items": tasks,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Get a task by ID",
)
async def get_task(
    task_id: int = Path(..., ge=1, description="Unique integer ID of the task"),
    db: AsyncSession = Depends(get_db),
):
    task = await task_service.get_task(
        db=db,
        task_id=task_id,
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
    summary="Update a task by ID",
)
@router.patch(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Partially update a task by ID",
)
async def update_task(
    task_data: TaskUpdate,
    task_id: int = Path(..., ge=1, description="Unique integer ID of the task"),
    db: AsyncSession = Depends(get_db),
):
    updated_task = await task_service.update_task(
        db=db,
        task=task_id,
        task_data=task_data,
    )

    if updated_task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    return updated_task


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a task by ID",
)
async def delete_task(
    task_id: int = Path(..., ge=1, description="Unique integer ID of the task"),
    db: AsyncSession = Depends(get_db),
):
    deleted = await task_service.delete_task(
        db=db,
        task=task_id,
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )