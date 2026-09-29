from pydantic import BaseModel, ConfigDict, Field, computed_field


class TaskStatusCounts(BaseModel):
    """Counts of tasks partitioned by status."""

    total: int = Field(..., ge=0, description="Total number of tasks")
    pending: int = Field(..., ge=0, description="Number of pending tasks")
    in_progress: int = Field(..., ge=0, description="Number of tasks in progress")
    completed: int = Field(..., ge=0, description="Number of completed tasks")
    cancelled: int = Field(..., ge=0, description="Number of cancelled tasks")

    model_config = ConfigDict(from_attributes=True)


class TaskPriorityCounts(BaseModel):
    """Counts of tasks partitioned by priority."""

    low: int = Field(..., ge=0, description="Number of low priority tasks")
    medium: int = Field(..., ge=0, description="Number of medium priority tasks")
    high: int = Field(..., ge=0, description="Number of high priority tasks")
    urgent: int = Field(..., ge=0, description="Number of urgent priority tasks")

    model_config = ConfigDict(from_attributes=True)


class TaskDueDateCounts(BaseModel):
    """
    Due date metrics based on UTC timestamps.

    Date boundary definitions:
    - overdue: Active tasks (not completed or cancelled) with due_date < current UTC time.
    - due_today: Active tasks with due_date between 00:00:00 and 23:59:59.999999 UTC today.
    - due_this_week: Active tasks with due_date between start of today and 7 days ahead (rolling 7-day window).
    - upcoming: Active tasks with due_date strictly greater than end of today (future days).
    """

    overdue: int = Field(..., ge=0, description="Tasks past due date that are not completed or cancelled")
    due_today: int = Field(..., ge=0, description="Active tasks due on the current UTC date")
    due_this_week: int = Field(..., ge=0, description="Active tasks due within 7 days from today")
    upcoming: int = Field(..., ge=0, description="Active tasks scheduled for future dates beyond today")

    model_config = ConfigDict(from_attributes=True)


class CompletionMetrics(BaseModel):
    """Productivity completion indicators."""

    total_completed: int = Field(..., ge=0, description="Total number of completed tasks")
    completion_percentage: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Percentage of total tasks completed (0.0 to 100.0, safely handled when total is 0)",
    )

    model_config = ConfigDict(from_attributes=True)


class CategoryTaskCount(BaseModel):
    """Task counts grouped by category."""

    category_id: int | None = Field(
        default=None,
        description="Category ID, or null for uncategorized tasks",
    )
    category_name: str = Field(
        ...,
        description="Category name, or 'Uncategorized'",
    )
    task_count: int = Field(
        ...,
        ge=0,
        description="Number of tasks in this category",
    )

    model_config = ConfigDict(from_attributes=True)


class CompletionTrendPoint(BaseModel):
    """A single date data point in the completion trend chart."""

    date: str = Field(..., description="Date formatted as YYYY-MM-DD")
    completed: int = Field(..., ge=0, description="Number of tasks completed on this date")

    model_config = ConfigDict(from_attributes=True)


class DashboardSummaryResponse(BaseModel):
    """Consolidated productivity summary for the authenticated user."""

    total_tasks: TaskStatusCounts = Field(..., description="Task counts by status")
    priority_summary: TaskPriorityCounts = Field(..., description="Task counts by priority")
    due_date_summary: TaskDueDateCounts = Field(..., description="Due date metrics")
    completion_metrics: CompletionMetrics = Field(..., description="Task completion rate and count")
    category_summary: list[CategoryTaskCount] = Field(
        ...,
        description="Task counts grouped by category, including uncategorized tasks",
    )
    completion_trend: list[CompletionTrendPoint] = Field(
        ...,
        description="Recent completed tasks grouped by date for charts",
    )

    @computed_field
    def tasks(self) -> TaskStatusCounts:
        """Alias property for total_tasks."""
        return self.total_tasks

    @computed_field
    def due_dates(self) -> TaskDueDateCounts:
        """Alias property for due_date_summary."""
        return self.due_date_summary

    model_config = ConfigDict(from_attributes=True)
