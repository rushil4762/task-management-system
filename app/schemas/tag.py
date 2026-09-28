from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TagBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, description="Tag name")

    @field_validator("name")
    @classmethod
    def validate_name_not_empty(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Tag name cannot be blank or only whitespace")
        return cleaned


class TagCreate(TagBase):
    pass


class TagUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
        description="Updated tag name",
    )

    @field_validator("name")
    @classmethod
    def validate_name_not_empty(cls, v: str | None) -> str | None:
        if v is not None:
            cleaned = v.strip()
            if not cleaned:
                raise ValueError("Tag name cannot be blank or only whitespace")
            return cleaned
        return None


class TagResponse(TagBase):
    id: int
    user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TaskTagsAttachRequest(BaseModel):
    tag_ids: list[int] = Field(
        ...,
        min_length=1,
        max_length=50,
        description="List of user tag IDs to associate with the task",
    )
