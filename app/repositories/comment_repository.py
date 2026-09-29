from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.comment import TaskComment


async def create_comment(
    db: AsyncSession,
    comment: TaskComment,
) -> TaskComment:
    try:
        db.add(comment)
        await db.commit()
        await db.refresh(comment)
        return comment
    except Exception:
        await db.rollback()
        raise


async def get_comment_by_id(
    db: AsyncSession,
    comment_id: int,
) -> TaskComment | None:
    query = (
        select(TaskComment)
        .options(joinedload(TaskComment.user))
        .where(TaskComment.id == comment_id)
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_comments_by_task_id(
    db: AsyncSession,
    task_id: int,
) -> list[TaskComment]:
    query = (
        select(TaskComment)
        .options(joinedload(TaskComment.user))
        .where(TaskComment.task_id == task_id)
        .order_by(TaskComment.created_at.asc())
    )
    result = await db.execute(query)
    return list(result.scalars().all())


async def update_comment(
    db: AsyncSession,
    comment: TaskComment,
) -> TaskComment:
    try:
        await db.commit()
        await db.refresh(comment)
        return comment
    except Exception:
        await db.rollback()
        raise


async def delete_comment(
    db: AsyncSession,
    comment: TaskComment,
) -> None:
    try:
        await db.delete(comment)
        await db.commit()
    except Exception:
        await db.rollback()
        raise
