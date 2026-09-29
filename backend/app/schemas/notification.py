from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.notification import NotificationType


class NotificationResponse(BaseModel):
    """Notification response entity schema."""

    id: int = Field(..., description="Unique notification identifier")
    user_id: int = Field(..., description="Recipient user identifier")
    task_id: int | None = Field(None, description="Optional associated task identifier")
    type: NotificationType = Field(..., description="Notification event type")
    title: str = Field(..., description="Brief notification headline")
    message: str = Field(..., description="Detailed notification message")
    is_read: bool = Field(..., description="Whether the notification has been read")
    created_at: datetime = Field(..., description="Timestamp when notification was triggered")

    model_config = ConfigDict(from_attributes=True)


class NotificationListResponse(BaseModel):
    """Paginated list of notifications for the user."""

    items: list[NotificationResponse] = Field(..., description="List of notification objects")
    total: int = Field(..., ge=0, description="Total matching notifications")
    unread_count: int = Field(..., ge=0, description="Total unread notifications for the user")
    limit: int = Field(..., ge=1, description="Pagination limit")
    offset: int = Field(..., ge=0, description="Pagination offset")

    model_config = ConfigDict(from_attributes=True)


class UnreadCountResponse(BaseModel):
    """Unread notifications count schema."""

    unread_count: int = Field(..., ge=0, description="Total unread notifications for the user")


class ReadAllResponse(BaseModel):
    """Response after marking all notifications as read."""

    message: str = Field(..., description="Status message")
    updated_count: int = Field(..., ge=0, description="Number of notifications marked as read")
