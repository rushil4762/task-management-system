from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.tag import (
    TagCreate,
    TagResponse,
    TagUpdate,
)
from app.services import tag_service

router = APIRouter(
    prefix="/tags",
    tags=["Tags"],
)


@router.post(
    "",
    response_model=TagResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new tag for the authenticated user",
)
async def create_tag(
    tag_data: TagCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await tag_service.create_tag(
        db=db,
        user_id=current_user.id,
        tag_data=tag_data,
    )


@router.get(
    "",
    response_model=list[TagResponse],
    summary="List all tags owned by the authenticated user",
)
async def list_tags(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await tag_service.get_tags(
        db=db,
        user_id=current_user.id,
    )


@router.get(
    "/{tag_id}",
    response_model=TagResponse,
    summary="Get an owned tag by ID",
)
async def get_tag(
    tag_id: int = Path(..., ge=1, description="Unique integer ID of the tag"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tag = await tag_service.get_tag(
        db=db,
        tag_id=tag_id,
        user_id=current_user.id,
    )
    if tag is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found",
        )
    return tag


@router.put(
    "/{tag_id}",
    response_model=TagResponse,
    summary="Update an owned tag by ID",
)
@router.patch(
    "/{tag_id}",
    response_model=TagResponse,
    summary="Partially update an owned tag by ID",
)
async def update_tag(
    tag_data: TagUpdate,
    tag_id: int = Path(..., ge=1, description="Unique integer ID of the tag"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    updated = await tag_service.update_tag(
        db=db,
        tag_id=tag_id,
        user_id=current_user.id,
        tag_data=tag_data,
    )
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found",
        )
    return updated


@router.delete(
    "/{tag_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an owned tag by ID",
)
async def delete_tag(
    tag_id: int = Path(..., ge=1, description="Unique integer ID of the tag"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    deleted = await tag_service.delete_tag(
        db=db,
        tag_id=tag_id,
        user_id=current_user.id,
    )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found",
        )
