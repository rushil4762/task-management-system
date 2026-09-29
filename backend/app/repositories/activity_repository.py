from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.activity import TaskActivity


async def create_activity(
    db: AsyncSession,
    activity: TaskActivity,
    commit: bool = True,
) -> TaskActivity:
    try:
        db.add(activity)
        if commit:
            await db.commit()
            await db.refresh(activity)
        return activity
    except Exception:
        if commit:
            await db.rollback()
        raise


async def get_activities_by_task_id(
    db: AsyncSession,
    task_id: int,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[TaskActivity], int]:
    # 1. Total count
    count_query = select(func.count(TaskActivity.id)).where(
        TaskActivity.task_id == task_id
    )
    count_res = await db.execute(count_query)
    total = count_res.scalar_one()

    # 2. Paginated activities ordered by newest first
    query = (
        select(TaskActivity)
        .options(joinedload(TaskActivity.user))
        .where(TaskActivity.task_id == task_id)
        .order_by(TaskActivity.created_at.desc(), TaskActivity.id.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(query)
    activities = list(result.scalars().all())

    return activities, total
