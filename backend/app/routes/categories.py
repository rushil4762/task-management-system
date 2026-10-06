from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User, UserRole
from app.schemas.category import (
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
)
from app.services import category_service

router = APIRouter(
    prefix="/categories",
    tags=["Categories"],
)


@router.post(
    "",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new category (CEO only)",
)
async def create_category(
    category_data: CategoryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role != UserRole.CEO:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only CEO can create categories",
        )

    return await category_service.create_category(
        db=db,
        user_id=current_user.id,
        category_data=category_data,
    )


@router.get(
    "",
    response_model=list[CategoryResponse],
    summary="List accessible categories",
)
async def list_categories(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    is_employee = current_user.role == UserRole.EMPLOYEE
    return await category_service.get_categories(
        db=db,
        user_id=current_user.id,
        is_employee=is_employee,
    )


@router.get(
    "/{category_id}",
    response_model=CategoryResponse,
    summary="Get category by ID",
)
async def get_category(
    category_id: int = Path(..., ge=1, description="Unique integer ID of the category"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    is_employee = current_user.role == UserRole.EMPLOYEE
    category = await category_service.get_category(
        db=db,
        category_id=category_id,
        user_id=current_user.id,
        is_employee=is_employee,
    )
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )
    return category


@router.put(
    "/{category_id}",
    response_model=CategoryResponse,
    summary="Update category (CEO only)",
)
@router.patch(
    "/{category_id}",
    response_model=CategoryResponse,
    summary="Partially update category (CEO only)",
)
async def update_category(
    category_data: CategoryUpdate,
    category_id: int = Path(..., ge=1, description="Unique integer ID of the category"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role != UserRole.CEO:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only CEO can edit categories",
        )

    updated = await category_service.update_category(
        db=db,
        category_id=category_id,
        user_id=current_user.id,
        category_data=category_data,
    )
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )
    return updated


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete category (CEO only)",
)
async def delete_category(
    category_id: int = Path(..., ge=1, description="Unique integer ID of the category"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role != UserRole.CEO:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only CEO can delete categories",
        )

    deleted = await category_service.delete_category(
        db=db,
        category_id=category_id,
        user_id=current_user.id,
    )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

