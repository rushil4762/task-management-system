from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class TaskActivityAction(str, Enum):
    TASK_CREATED = "task_created"
    TASK_UPDATED = "task_updated"
    STATUS_CHANGED = "status_changed"
    PRIORITY_CHANGED = "priority_changed"
    DUE_DATE_CHANGED = "due_date_changed"
    TASK_COMPLETED = "task_completed"
    TASK_REOPENED = "task_reopened"
    TASK_ASSIGNED = "task_assigned"
    CATEGORY_CHANGED = "category_changed"
    TAG_ADDED = "tag_added"
    TAG_REMOVED = "tag_removed"
    COMMENT_ADDED = "comment_added"


class ActivityActor(BaseModel):
    id: int
    name: str
    email: str

    model_config = ConfigDict(from_attributes=True)


class ActivityResponse(BaseModel):
    id: int
    task_id: int
    user_id: int | None = None
    action: str
    activity_type: str | None = None
    message: str | None = None
    description: str
    metadata: dict[str, Any] | None = Field(default=None, validation_alias="meta_data")
    created_at: datetime
    user: ActivityActor | None = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    @model_validator(mode="after")
    def populate_fields(self) -> "ActivityResponse":
        if not self.activity_type:
            self.activity_type = self.action
        if not self.message:
            self.message = self.description
        return self



class ActivityListResponse(BaseModel):
    items: list[ActivityResponse] = Field(
        ...,
        description="Paginated list of task activities",
    )
    total: int = Field(
        ...,
        ge=0,
        description="Total number of activity entries recorded for this task",
    )
    limit: int = Field(
        ...,
        ge=1,
        description="Limit parameter applied to request",
    )
    offset: int = Field(
        ...,
        ge=0,
        description="Offset parameter applied to request",
    )
