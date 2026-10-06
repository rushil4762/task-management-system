from datetime import date, datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity import TaskActivity
from app.repositories import dashboard_repository
from app.schemas.dashboard import (
    CategoryTaskCount,
    CompletionMetrics,
    CompletionTrendPoint,
    DashboardSummaryResponse,
    TaskDueDateCounts,
    TaskPriorityCounts,
    TaskStatusCounts,
)
from app.services import activity_service


async def get_dashboard_summary(
    db: AsyncSession,
    user_id: int,
    is_employee: bool = False,
) -> DashboardSummaryResponse:
    """
    Generate comprehensive productivity summary for the authenticated user.
    Aggregates status counts, priority distribution, due date urgency,
    completion metrics, category distribution, and recent completion trend.
    """
    # 1. Fetch task aggregates (status, priority, due dates, completion)
    metrics = await dashboard_repository.get_task_metrics(
        db=db,
        user_id=user_id,
        is_employee=is_employee,
    )

    # 2. Fetch category metrics (user-scoped categories + uncategorized)
    categories_raw = await dashboard_repository.get_category_metrics(
        db=db,
        user_id=user_id,
        is_employee=is_employee,
    )
    category_summary = [
        CategoryTaskCount(
            category_id=cat["category_id"],
            category_name=cat["category_name"],
            task_count=cat["task_count"],
        )
        for cat in categories_raw
    ]

    # 3. Fetch completion trend for the last 14 days for quick chart preview
    now_utc = datetime.now(timezone.utc)
    recent_trend_raw = await dashboard_repository.get_completion_trend(
        db=db,
        user_id=user_id,
        start_date=(now_utc - timedelta(days=14)).date(),
        end_date=now_utc.date(),
        is_employee=is_employee,
    )
    completion_trend = [
        CompletionTrendPoint(
            date=point["date"],
            completed=point["completed"],
        )
        for point in recent_trend_raw
    ]

    return DashboardSummaryResponse(
        total_tasks=TaskStatusCounts(**metrics["status"]),
        priority_summary=TaskPriorityCounts(**metrics["priorities"]),
        due_date_summary=TaskDueDateCounts(**metrics["due_dates"]),
        completion_metrics=CompletionMetrics(**metrics["completion"]),
        category_summary=category_summary,
        completion_trend=completion_trend,
    )


async def get_completion_trend(
    db: AsyncSession,
    user_id: int,
    start_date: date | None = None,
    end_date: date | None = None,
    days: int = 30,
    is_employee: bool = False,
) -> list[CompletionTrendPoint]:
    """
    Get completed task counts grouped by date within a validated date window.
    """
    now_date = datetime.now(timezone.utc).date()

    if start_date is not None and end_date is not None:
        if start_date > end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="start_date must be less than or equal to end_date",
            )
    elif start_date is not None and end_date is None:
        end_date = now_date
        if start_date > end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="start_date cannot be in the future when end_date is not specified",
            )
    elif start_date is None and end_date is not None:
        start_date = end_date - timedelta(days=days)
    else:
        end_date = now_date
        start_date = now_date - timedelta(days=days)

    trend_raw = await dashboard_repository.get_completion_trend(
        db=db,
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        is_employee=is_employee,
    )

    return [
        CompletionTrendPoint(
            date=point["date"],
            completed=point["completed"],
        )
        for point in trend_raw
    ]


async def get_recent_activity(
    db: AsyncSession,
    user_id: int,
    limit: int = 10,
    offset: int = 0,
) -> tuple[list[TaskActivity], int]:
    """
    Fetch recent task activities for tasks authorized to the authenticated user.
    """
    return await activity_service.get_recent_activities_for_user(
        db=db,
        user_id=user_id,
        limit=limit,
        offset=offset,
    )
