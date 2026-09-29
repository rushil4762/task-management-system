from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.activity import ActivityListResponse
from app.schemas.dashboard import CompletionTrendPoint, DashboardSummaryResponse
from app.services import dashboard_service

router = APIRouter(
    prefix="/dashboard",
    tags=["Productivity Dashboard"],
)


@router.get(
    "/summary",
    response_model=DashboardSummaryResponse,
    summary="Get productivity dashboard summary for the current user",
)
async def get_dashboard_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns consolidated productivity metrics for the currently authenticated user:
    - **Total Tasks**: breakdown by status (`total`, `pending`, `in_progress`, `completed`, `cancelled`)
    - **Priority Summary**: counts for `low`, `medium`, `high`, `urgent`
    - **Due Date Information**: `overdue`, `due_today`, `due_this_week`, `upcoming`
    - **Completion Metrics**: `total_completed`, `completion_percentage` (zero-division safe)
    - **Category Summary**: task counts grouped by category, including uncategorized tasks
    - **Productivity Trend**: recent 14-day completion chart data points
    """
    return await dashboard_service.get_dashboard_summary(
        db=db,
        user_id=current_user.id,
    )


@router.get(
    "/completion-trend",
    response_model=list[CompletionTrendPoint],
    summary="Get productivity completion trend grouped by date",
)
async def get_completion_trend(
    start_date: date | None = Query(
        default=None,
        description="Filter completed tasks from this date (YYYY-MM-DD)",
    ),
    end_date: date | None = Query(
        default=None,
        description="Filter completed tasks up to this date (YYYY-MM-DD)",
    ),
    days: int = Query(
        default=30,
        ge=1,
        le=365,
        description="Number of days to look back if date range is not specified",
    ),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns completed task counts aggregated by date using database grouping.
    Accepts optional `start_date` and `end_date` (or defaults to `days` lookback).
    """
    return await dashboard_service.get_completion_trend(
        db=db,
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
        days=days,
    )


@router.get(
    "/recent-activity",
    response_model=ActivityListResponse,
    summary="Get recent activities for the authenticated user's tasks",
)
async def get_recent_activity(
    limit: int = Query(
        default=10,
        ge=1,
        le=100,
        description="Maximum number of activities to return (1-100)",
    ),
    offset: int = Query(
        default=0,
        ge=0,
        description="Number of activities to skip",
    ),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns recent task activities across all tasks the authenticated user is authorized
    to view (tasks owned by or assigned to the user), ordered newest first.
    """
    activities, total = await dashboard_service.get_recent_activity(
        db=db,
        user_id=current_user.id,
        limit=limit,
        offset=offset,
    )
    return {
        "items": activities,
        "total": total,
        "limit": limit,
        "offset": offset,
    }
