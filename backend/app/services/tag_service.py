from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tag import Tag
from app.repositories import tag_repository
from app.schemas.tag import TagCreate, TagUpdate


async def create_tag(
    db: AsyncSession,
    user_id: int,
    tag_data: TagCreate,
) -> Tag:
    existing = await tag_repository.get_tag_by_name(
        db=db,
        name=tag_data.name,
        user_id=user_id,
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tag with this name already exists",
        )

    tag = Tag(
        name=tag_data.name,
        user_id=user_id,
    )
    return await tag_repository.create_tag(db, tag)


async def get_tag(
    db: AsyncSession,
    tag_id: int,
    user_id: int,
) -> Tag | None:
    return await tag_repository.get_tag_by_id(
        db=db,
        tag_id=tag_id,
        user_id=user_id,
    )


async def get_tags(
    db: AsyncSession,
    user_id: int,
) -> list[Tag]:
    return await tag_repository.get_tags(
        db=db,
        user_id=user_id,
    )


async def update_tag(
    db: AsyncSession,
    tag_id: int,
    user_id: int,
    tag_data: TagUpdate,
) -> Tag | None:
    tag = await tag_repository.get_tag_by_id(
        db=db,
        tag_id=tag_id,
        user_id=user_id,
    )
    if tag is None:
        return None

    update_dict = tag_data.model_dump(exclude_unset=True)

    if "name" in update_dict and update_dict["name"] != tag.name:
        existing = await tag_repository.get_tag_by_name(
            db=db,
            name=update_dict["name"],
            user_id=user_id,
        )
        if existing is not None and existing.id != tag.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tag with this name already exists",
            )
        tag.name = update_dict["name"]

    return await tag_repository.update_tag(db, tag)


async def delete_tag(
    db: AsyncSession,
    tag_id: int,
    user_id: int,
) -> bool:
    tag = await tag_repository.get_tag_by_id(
        db=db,
        tag_id=tag_id,
        user_id=user_id,
    )
    if tag is None:
        return False

    await tag_repository.delete_tag(db, tag)
    return True
