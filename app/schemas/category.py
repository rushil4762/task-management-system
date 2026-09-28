from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Category name")
    description: str | None = Field(default=None, max_length=1000, description="Category description")

    @field_validator("name")
    @classmethod
    def validate_name_not_empty(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Category name cannot be blank or only whitespace")
        return cleaned

    @field_validator("description")
    @classmethod
    def clean_description(cls, v: str | None) -> str | None:
        if v is not None:
            cleaned = v.strip()
            return cleaned if cleaned else None
        return None


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Updated category name",
    )
    description: str | None = Field(
        default=None,
        max_length=1000,
        description="Updated category description (null to clear)",
    )

    @field_validator("name")
    @classmethod
    def validate_name_not_empty(cls, v: str | None) -> str | None:
        if v is not None:
            cleaned = v.strip()
            if not cleaned:
                raise ValueError("Category name cannot be blank or only whitespace")
            return cleaned
        return None


class CategoryResponse(CategoryBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
