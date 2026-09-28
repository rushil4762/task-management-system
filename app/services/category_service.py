from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.repositories import category_repository
from app.schemas.category import CategoryCreate, CategoryUpdate


async def create_category(
    db: AsyncSession,
    user_id: int,
    category_data: CategoryCreate,
) -> Category:
    existing = await category_repository.get_category_by_name(
        db=db,
        name=category_data.name,
        user_id=user_id,
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category with this name already exists",
        )

    category = Category(
        name=category_data.name,
        description=category_data.description,
        user_id=user_id,
    )
    return await category_repository.create_category(db, category)


async def get_category(
    db: AsyncSession,
    category_id: int,
    user_id: int,
) -> Category | None:
    return await category_repository.get_category_by_id(
        db=db,
        category_id=category_id,
        user_id=user_id,
    )


async def get_categories(
    db: AsyncSession,
    user_id: int,
) -> list[Category]:
    return await category_repository.get_categories(
        db=db,
        user_id=user_id,
    )


async def update_category(
    db: AsyncSession,
    category_id: int,
    user_id: int,
    category_data: CategoryUpdate,
) -> Category | None:
    category = await category_repository.get_category_by_id(
        db=db,
        category_id=category_id,
        user_id=user_id,
    )
    if category is None:
        return None

    update_dict = category_data.model_dump(exclude_unset=True)

    if "name" in update_dict and update_dict["name"] != category.name:
        existing = await category_repository.get_category_by_name(
            db=db,
            name=update_dict["name"],
            user_id=user_id,
        )
        if existing is not None and existing.id != category.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category with this name already exists",
            )
        category.name = update_dict["name"]

    if "description" in update_dict:
        category.description = update_dict["description"]

    category.updated_at = datetime.now(timezone.utc)
    return await category_repository.update_category(db, category)


async def delete_category(
    db: AsyncSession,
    category_id: int,
    user_id: int,
) -> bool:
    category = await category_repository.get_category_by_id(
        db=db,
        category_id=category_id,
        user_id=user_id,
    )
    if category is None:
        return False

    await category_repository.delete_category(db, category)
    return True
