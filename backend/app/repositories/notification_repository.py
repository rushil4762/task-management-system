from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification, NotificationType


async def create_notification(
    db: AsyncSession,
    notification: Notification,
    commit: bool = True,
) -> Notification | None:
    """
    Persist a new notification. If a unique constraint violation occurs
    (duplicate event for user/task/type/event_key), safely rolls back and
    returns the existing record.
    """
    try:
        db.add(notification)
        if commit:
            await db.commit()
            await db.refresh(notification)
        return notification
    except IntegrityError:
        if commit:
            await db.rollback()
        # Retrieve existing notification to prevent duplicate error
        if notification.event_key:
            return await get_notification_by_event(
                db=db,
                user_id=notification.user_id,
                task_id=notification.task_id,
                notification_type=notification.type,
                event_key=notification.event_key,
            )
        return None
    except Exception:
        if commit:
            await db.rollback()
        raise


async def get_notification_by_id(
    db: AsyncSession,
    notification_id: int,
    user_id: int | None = None,
) -> Notification | None:
    """
    Retrieve notification by ID, optionally restricted to a specific user.
    """
    query = select(Notification).where(Notification.id == notification_id)
    if user_id is not None:
        query = query.where(Notification.user_id == user_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_notification_by_event(
    db: AsyncSession,
    user_id: int,
    task_id: int | None,
    notification_type: NotificationType,
    event_key: str,
) -> Notification | None:
    """
    Retrieve an existing notification matching the exact deduplication signature.
    """
    query = select(Notification).where(
        Notification.user_id == user_id,
        Notification.task_id == task_id,
        Notification.type == notification_type,
        Notification.event_key == event_key,
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_notifications_for_user(
    db: AsyncSession,
    user_id: int,
    is_read: bool | None = None,
    notification_type: NotificationType | None = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[Notification], int, int]:
    """
    Retrieve paginated notifications for the specified user with optional filters.
    Returns: (items, total_filtered_count, total_unread_count)
    """
    base_filter = [Notification.user_id == user_id]

    if is_read is not None:
        base_filter.append(Notification.is_read == is_read)
    if notification_type is not None:
        base_filter.append(Notification.type == notification_type)

    # 1. Total matching filtered count
    count_query = select(func.count(Notification.id)).where(*base_filter)
    count_res = await db.execute(count_query)
    total = count_res.scalar_one()

    # 2. Total user unread count (unfiltered by pagination or type)
    unread_query = select(func.count(Notification.id)).where(
        Notification.user_id == user_id,
        Notification.is_read == False,  # noqa: E712
    )
    unread_res = await db.execute(unread_query)
    unread_count = unread_res.scalar_one()

    # 3. Paginated items newest first
    query = (
        select(Notification)
        .where(*base_filter)
        .order_by(Notification.created_at.desc(), Notification.id.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(query)
    items = list(result.scalars().all())

    return items, total, unread_count


async def get_unread_count(
    db: AsyncSession,
    user_id: int,
) -> int:
    """
    Return count of unread notifications for the specified user.
    """
    query = select(func.count(Notification.id)).where(
        Notification.user_id == user_id,
        Notification.is_read == False,  # noqa: E712
    )
    result = await db.execute(query)
    return result.scalar_one()


async def mark_as_read(
    db: AsyncSession,
    notification: Notification,
) -> Notification:
    """
    Mark an individual notification as read.
    """
    notification.is_read = True
    await db.commit()
    await db.refresh(notification)
    return notification


async def mark_all_as_read(
    db: AsyncSession,
    user_id: int,
) -> int:
    """
    Bulk mark all unread notifications belonging to the user as read.
    Returns the count of modified rows.
    """
    stmt = (
        update(Notification)
        .where(
            Notification.user_id == user_id,
            Notification.is_read == False,  # noqa: E712
        )
        .values(is_read=True)
    )
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount or 0
