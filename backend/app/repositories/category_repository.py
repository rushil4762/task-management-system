from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category


async def create_category(
    db: AsyncSession,
    category: Category,
) -> Category:
    try:
        db.add(category)
        await db.commit()
        await db.refresh(category)
        return category
    except Exception:
        await db.rollback()
        raise


async def get_category_by_id(
    db: AsyncSession,
    category_id: int,
    user_id: int | None = None,
) -> Category | None:
    query = select(Category).where(Category.id == category_id)
    if user_id is not None:
        query = query.where(Category.user_id == user_id)

    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_category_by_name(
    db: AsyncSession,
    name: str,
    user_id: int,
) -> Category | None:
    query = select(Category).where(
        Category.user_id == user_id,
        Category.name == name,
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_categories(
    db: AsyncSession,
    user_id: int | None = None,
) -> list[Category]:
    query = select(Category).order_by(Category.name.asc())
    if user_id is not None:
        query = query.where(Category.user_id == user_id)
    result = await db.execute(query)
    return list(result.scalars().all())


async def update_category(
    db: AsyncSession,
    category: Category,
) -> Category:
    try:
        await db.commit()
        await db.refresh(category)
        return category
    except Exception:
        await db.rollback()
        raise


async def delete_category(
    db: AsyncSession,
    category: Category,
) -> None:
    try:
        await db.delete(category)
        await db.commit()
    except Exception:
        await db.rollback()
        raise
