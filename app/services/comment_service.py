from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity import TaskActivity
from app.models.comment import TaskComment
from app.repositories import (
    activity_repository,
    comment_repository,
    task_repository,
)
from app.schemas.activity import TaskActivityAction
from app.schemas.comment import CommentCreate, CommentUpdate


async def add_comment(
    db: AsyncSession,
    task_id: int,
    user_id: int,
    comment_data: CommentCreate,
) -> TaskComment:
    # 1. Authorize: current user must be owner or assignee of the task
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

    # 2. Persist comment
    comment = TaskComment(
        task_id=task_id,
        user_id=user_id,
        content=comment_data.content,
    )
    created_comment = await comment_repository.create_comment(db, comment)

    # 3. Append activity record for comment addition
    activity = TaskActivity(
        task_id=task_id,
        user_id=user_id,
        action=TaskActivityAction.COMMENT_ADDED.value,
        description="A new comment was added",
    )
    await activity_repository.create_activity(db, activity, commit=True)

    # Refresh comment with user relation eagerly loaded
    fresh = await comment_repository.get_comment_by_id(db, created_comment.id)
    return fresh or created_comment


async def get_comments_for_task(
    db: AsyncSession,
    task_id: int,
    user_id: int,
) -> list[TaskComment]:
    # Authorize: user must have access to task
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

    return await comment_repository.get_comments_by_task_id(db, task_id)


async def update_comment(
    db: AsyncSession,
    comment_id: int,
    user_id: int,
    comment_data: CommentUpdate,
) -> TaskComment:
    comment = await comment_repository.get_comment_by_id(db, comment_id)
    if comment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found",
        )

    # Authorize: only author can edit their own comment
    if comment.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to edit this comment",
        )

    comment.content = comment_data.content
    comment.updated_at = datetime.now(timezone.utc)
    return await comment_repository.update_comment(db, comment)


async def delete_comment(
    db: AsyncSession,
    comment_id: int,
    user_id: int,
) -> bool:
    comment = await comment_repository.get_comment_by_id(db, comment_id)
    if comment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found",
        )

    # Authorize: only author can delete their own comment
    if comment.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this comment",
        )

    await comment_repository.delete_comment(db, comment)
    return True
