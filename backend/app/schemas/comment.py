from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CommentAuthor(BaseModel):
    id: int
    name: str
    email: str

    model_config = ConfigDict(from_attributes=True)


class CommentBase(BaseModel):
    content: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Comment text content",
    )

    @field_validator("content")
    @classmethod
    def validate_content_not_empty(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Comment content cannot be blank or only whitespace")
        return cleaned


class CommentCreate(CommentBase):
    pass


class CommentUpdate(BaseModel):
    content: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Updated comment text content",
    )

    @field_validator("content")
    @classmethod
    def validate_content_not_empty(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Comment content cannot be blank or only whitespace")
        return cleaned


class CommentResponse(CommentBase):
    id: int
    task_id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    user: CommentAuthor | None = None

    model_config = ConfigDict(from_attributes=True)
