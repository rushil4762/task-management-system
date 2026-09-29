from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification, NotificationType
from app.repositories import notification_repository


async def create_notification(
    db: AsyncSession,
    user_id: int,
    type: NotificationType,
    title: str,
    message: str,
    task_id: int | None = None,
    event_key: str | None = None,
) -> Notification | None:
    """
    Centralized notification creator with duplicate prevention.
    If event_key is provided and an existing notification with the same
    (user_id, task_id, type, event_key) is found, returns the existing record
    without creating a duplicate.
    """
    if event_key is not None:
        existing = await notification_repository.get_notification_by_event(
            db=db,
            user_id=user_id,
            task_id=task_id,
            notification_type=type,
            event_key=event_key,
        )
        if existing is not None:
            return None

    notification = Notification(

        user_id=user_id,
        task_id=task_id,
        type=type,
        title=title,
        message=message,
        event_key=event_key,
        is_read=False,
    )
    return await notification_repository.create_notification(db, notification)


async def get_notifications(
    db: AsyncSession,
    user_id: int,
    is_read: bool | None = None,
    notification_type: NotificationType | None = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[Notification], int, int]:
    """
    Get paginated notifications scoped to the authenticated user.
    """
    return await notification_repository.get_notifications_for_user(
        db=db,
        user_id=user_id,
        is_read=is_read,
        notification_type=notification_type,
        limit=limit,
        offset=offset,
    )


async def get_unread_count(
    db: AsyncSession,
    user_id: int,
) -> int:
    """
    Get unread notification count for the authenticated user.
    """
    return await notification_repository.get_unread_count(db=db, user_id=user_id)


async def mark_as_read(
    db: AsyncSession,
    notification_id: int,
    user_id: int,
) -> Notification:
    """
    Mark an individual notification as read.
    Validates ownership: fails with 404 if not found or 403 if belonging to another user.
    """
    notification = await notification_repository.get_notification_by_id(
        db=db,
        notification_id=notification_id,
    )
    if notification is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    if notification.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify another user's notification",
        )

    return await notification_repository.mark_as_read(db=db, notification=notification)


async def mark_all_as_read(
    db: AsyncSession,
    user_id: int,
) -> int:
    """
    Mark all unread notifications belonging to the user as read.
    """
    return await notification_repository.mark_all_as_read(db=db, user_id=user_id)
