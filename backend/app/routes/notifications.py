from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.notification import NotificationType
from app.models.user import User
from app.schemas.notification import (
    NotificationListResponse,
    NotificationResponse,
    ReadAllResponse,
    UnreadCountResponse,
)
from app.services import notification_service

router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"],
)


@router.get(
    "",
    response_model=NotificationListResponse,
    summary="List notifications for current authenticated user",
)
async def list_notifications(
    is_read: bool | None = Query(
        default=None,
        description="Filter notifications by read status (true/false)",
    ),
    type: NotificationType | None = Query(
        default=None,
        description="Filter notifications by type",
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of notifications to return",
    ),
    offset: int = Query(
        default=0,
        ge=0,
        description="Number of notifications to skip",
    ),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve paginated notifications for the current authenticated user,
    ordered newest first, with optional filtering by read status and type.
    """
    items, total, unread_count = await notification_service.get_notifications(
        db=db,
        user_id=current_user.id,
        is_read=is_read,
        notification_type=type,
        limit=limit,
        offset=offset,
    )
    return {
        "items": items,
        "total": total,
        "unread_count": unread_count,
        "limit": limit,
        "offset": offset,
    }


@router.get(
    "/unread-count",
    response_model=UnreadCountResponse,
    summary="Get unread notification count for current user",
)
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns the total number of unread notifications strictly scoped to the authenticated user.
    """
    count = await notification_service.get_unread_count(
        db=db,
        user_id=current_user.id,
    )
    return {"unread_count": count}


@router.patch(
    "/read-all",
    response_model=ReadAllResponse,
    summary="Mark all unread notifications as read for current user",
)
async def mark_all_notifications_as_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Bulk update marking all unread notifications belonging to the authenticated user as read.
    """
    updated_count = await notification_service.mark_all_as_read(
        db=db,
        user_id=current_user.id,
    )
    return {
        "message": "All unread notifications marked as read",
        "updated_count": updated_count,
    }


@router.patch(
    "/{id}/read",
    response_model=NotificationResponse,
    summary="Mark a specific notification as read",
)
async def mark_notification_as_read(
    id: int = Path(..., ge=1, description="Notification ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Marks a single notification as read if it belongs to the authenticated user.
    """
    return await notification_service.mark_as_read(
        db=db,
        notification_id=id,
        user_id=current_user.id,
    )
