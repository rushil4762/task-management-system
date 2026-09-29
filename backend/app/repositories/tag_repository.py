from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tag import Tag


async def create_tag(
    db: AsyncSession,
    tag: Tag,
) -> Tag:
    try:
        db.add(tag)
        await db.commit()
        await db.refresh(tag)
        return tag
    except Exception:
        await db.rollback()
        raise


async def get_tag_by_id(
    db: AsyncSession,
    tag_id: int,
    user_id: int | None = None,
) -> Tag | None:
    query = select(Tag).where(Tag.id == tag_id)
    if user_id is not None:
        query = query.where(Tag.user_id == user_id)

    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_tag_by_name(
    db: AsyncSession,
    name: str,
    user_id: int,
) -> Tag | None:
    query = select(Tag).where(
        Tag.user_id == user_id,
        Tag.name == name,
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_tags(
    db: AsyncSession,
    user_id: int,
) -> list[Tag]:
    query = (
        select(Tag)
        .where(Tag.user_id == user_id)
        .order_by(Tag.name.asc())
    )
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_tags_by_ids(
    db: AsyncSession,
    tag_ids: list[int],
    user_id: int,
) -> list[Tag]:
    if not tag_ids:
        return []
    query = select(Tag).where(
        Tag.id.in_(tag_ids),
        Tag.user_id == user_id,
    )
    result = await db.execute(query)
    return list(result.scalars().all())


async def update_tag(
    db: AsyncSession,
    tag: Tag,
) -> Tag:
    try:
        await db.commit()
        await db.refresh(tag)
        return tag
    except Exception:
        await db.rollback()
        raise


async def delete_tag(
    db: AsyncSession,
    tag: Tag,
) -> None:
    try:
        await db.delete(tag)
        await db.commit()
    except Exception:
        await db.rollback()
        raise
