from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.activity import ActivityListResponse
from app.services import activity_service

router = APIRouter(
    tags=["Activity History"],
)


@router.get(
    "/tasks/{task_id}/activities",
    response_model=ActivityListResponse,
    summary="Get paginated activity history for a task",
)
async def get_task_activities(
    task_id: int = Path(..., ge=1, description="Unique integer ID of the task"),
    limit: int = Query(
        default=20,
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
    activities, total = await activity_service.get_activities_for_task(
        db=db,
        task_id=task_id,
        user_id=current_user.id,
        role=current_user.role,
        limit=limit,
        offset=offset,
    )
    return {
        "items": activities,
        "total": total,
        "limit": limit,
        "offset": offset,
    }
