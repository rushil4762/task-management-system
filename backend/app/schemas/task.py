from datetime import datetime
from enum import Enum
from typing import List, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.task import TaskPriority, TaskStatus
from app.schemas.category import CategoryResponse
from app.schemas.tag import TagResponse
from app.schemas.user import UserResponse


class TaskSortBy(str, Enum):
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    DUE_DATE = "due_date"
    PRIORITY = "priority"
    TITLE = "title"
    ID = "id"
    STATUS = "status"


class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"


class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Task title")
    description: str | None = Field(default=None, max_length=5000, description="Detailed task description")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="Current status of the task")
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM, description="Priority level of the task")
    due_date: datetime | None = Field(default=None, description="Due date and time with timezone")
    category_id: int | None = Field(default=None, description="Optional category ID")
    assigned_to_id: int | None = Field(default=None, description="Optional assigned user ID")
    tag_ids: list[int] | None = Field(default=None, description="Optional tag IDs to attach")

    @field_validator("title")
    @classmethod
    def validate_title_not_empty(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Task title cannot be blank or only whitespace")
        return cleaned

    @field_validator("description")
    @classmethod
    def clean_description(cls, v: str | None) -> str | None:
        if v is not None:
            cleaned = v.strip()
            return cleaned if cleaned else None
        return None


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
        description="Updated task title",
    )
    description: str | None = Field(
        default=None,
        max_length=5000,
        description="Updated task description (null to clear)",
    )
    status: TaskStatus | None = Field(
        default=None,
        description="Updated status",
    )
    priority: TaskPriority | None = Field(
        default=None,
        description="Updated priority",
    )
    due_date: datetime | None = Field(
        default=None,
        description="Updated due date (null to clear)",
    )
    category_id: int | None = Field(
        default=None,
        description="Updated category ID (null to clear)",
    )
    assigned_to_id: int | None = Field(
        default=None,
        description="Updated assignee user ID (null to clear)",
    )
    tag_ids: list[int] | None = Field(
        default=None,
        description="Updated list of tag IDs to replace current tags",
    )

    @field_validator("title")
    @classmethod
    def validate_title_not_empty(cls, v: str | None) -> str | None:
        if v is not None:
            cleaned = v.strip()
            if not cleaned:
                raise ValueError("Task title cannot be blank or only whitespace")
            return cleaned
        return None


class TaskResponse(BaseModel):
    id: int
    title: str
    description: str | None
    status: TaskStatus
    priority: TaskPriority
    due_date: datetime | None
    completed_at: datetime | None
    user_id: int
    category_id: int | None = None
    assigned_to_id: int | None = None
    category: CategoryResponse | None = None
    tags: List[TagResponse] = []
    assignee: UserResponse | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TaskListResponse(BaseModel):
    items: list[TaskResponse]
    total: int
    limit: int
    offset: int


class BulkDeleteRequest(BaseModel):
    task_ids: list[int] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="List of integer task IDs to delete",
    )


class BulkDeleteResponse(BaseModel):
    deleted_count: int = Field(..., description="Number of tasks successfully deleted")
    message: str = Field(..., description="Operation summary message")


class TaskAssignRequest(BaseModel):
    assigned_to_id: int | None = Field(
        default=None,
        description="Employee user ID to assign the task to, or null to unassign",
    )