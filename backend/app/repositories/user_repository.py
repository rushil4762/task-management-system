from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole


async def create_user(
    db: AsyncSession,
    user: User,
) -> User:
    try:
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user
    except Exception:
        await db.rollback()
        raise


async def get_user_by_id(
    db: AsyncSession,
    user_id: int,
) -> User | None:
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    return result.scalar_one_or_none()


async def get_user_by_email(
    db: AsyncSession,
    email: str,
) -> User | None:
    result = await db.execute(
        select(User).where(func.lower(User.email) == email.strip().lower())
    )
    return result.scalar_one_or_none()


async def get_active_employees(
    db: AsyncSession,
) -> list[User]:
    result = await db.execute(
        select(User)
        .where(
            User.role == UserRole.EMPLOYEE,
            User.is_active.is_(True),
        )
        .order_by(User.name.asc())
    )
    return list(result.scalars().all())


async def update_user(
    db: AsyncSession,
    user: User,
) -> User:
    try:
        await db.commit()
        await db.refresh(user)
        return user
    except Exception:
        await db.rollback()
        raise

