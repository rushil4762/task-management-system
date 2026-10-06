from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User, UserRole
from app.repositories import user_repository
from app.schemas.user import EmployeeResponse

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.get(
    "/employees",
    response_model=list[EmployeeResponse],
    status_code=status.HTTP_200_OK,
    summary="Get active employees (CEO only)",
)
async def get_active_employees(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve all active employees for task assignment and management.
    Restricted to CEO users only.
    """
    if current_user.role != UserRole.CEO:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only CEO can access employee list",
        )

    employees = await user_repository.get_active_employees(db=db)
    return employees
