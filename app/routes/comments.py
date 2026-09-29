from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.comment import (
    CommentCreate,
    CommentResponse,
    CommentUpdate,
)
from app.services import comment_service

router = APIRouter(
    tags=["Comments"],
)


@router.post(
    "/tasks/{task_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a new comment to a task",
)
async def add_comment(
    comment_data: CommentCreate,
    task_id: int = Path(..., ge=1, description="Unique integer ID of the task"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await comment_service.add_comment(
        db=db,
        task_id=task_id,
        user_id=current_user.id,
        comment_data=comment_data,
    )


@router.get(
    "/tasks/{task_id}/comments",
    response_model=list[CommentResponse],
    summary="List all comments for a task",
)
async def get_comments_for_task(
    task_id: int = Path(..., ge=1, description="Unique integer ID of the task"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await comment_service.get_comments_for_task(
        db=db,
        task_id=task_id,
        user_id=current_user.id,
    )


@router.put(
    "/comments/{comment_id}",
    response_model=CommentResponse,
    summary="Edit an owned comment",
)
@router.patch(
    "/comments/{comment_id}",
    response_model=CommentResponse,
    summary="Partially edit an owned comment",
)
async def update_comment(
    comment_data: CommentUpdate,
    comment_id: int = Path(..., ge=1, description="Unique integer ID of the comment"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await comment_service.update_comment(
        db=db,
        comment_id=comment_id,
        user_id=current_user.id,
        comment_data=comment_data,
    )


@router.delete(
    "/comments/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an owned comment",
)
async def delete_comment(
    comment_id: int = Path(..., ge=1, description="Unique integer ID of the comment"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await comment_service.delete_comment(
        db=db,
        comment_id=comment_id,
        user_id=current_user.id,
    )
