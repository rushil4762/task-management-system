from datetime import datetime, timezone
from typing import TYPE_CHECKING, List

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.task import Task
    from app.models.user import User

task_tags = Table(
    "task_tags",
    Base.metadata,
    Column(
        "task_id",
        Integer,
        ForeignKey("tasks.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "tag_id",
        Integer,
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Index("ix_task_tags_task_id", "task_id"),
    Index("ix_task_tags_tag_id", "tag_id"),
)


class Tag(Base):
    __tablename__ = "tags"

    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_tags_user_name"),
        Index("ix_tags_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="tags",
    )

    tasks: Mapped[List["Task"]] = relationship(
        "Task",
        secondary=task_tags,
        back_populates="tags",
    )

    def __repr__(self) -> str:
        return f"<Tag id={self.id} name={self.name!r} user_id={self.user_id}>"
