from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity import TaskActivity
from app.repositories import activity_repository, task_repository


async def get_activities_for_task(
    db: AsyncSession,
    task_id: int,
    user_id: int,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[TaskActivity], int]:
    # Authorize: user must have access to task (owner or assignee)
    task = await task_repository.get_task_by_id(
        db=db,
        task_id=task_id,
        user_id=user_id,
        allow_assigned=True,
    )
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    return await activity_repository.get_activities_by_task_id(
        db=db,
        task_id=task_id,
        limit=limit,
        offset=offset,
    )


async def get_recent_activities_for_user(
    db: AsyncSession,
    user_id: int,
    limit: int = 10,
    offset: int = 0,
) -> tuple[list[TaskActivity], int]:
    return await activity_repository.get_recent_activities_for_user(
        db=db,
        user_id=user_id,
        limit=limit,
        offset=offset,
    )

