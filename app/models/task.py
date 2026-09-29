from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, List

from sqlalchemy import DateTime, Enum as SQLEnum, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.tag import task_tags

if TYPE_CHECKING:
    from app.models.activity import TaskActivity
    from app.models.category import Category
    from app.models.comment import TaskComment
    from app.models.tag import Tag
    from app.models.user import User



class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Task(Base):
    __tablename__ = "tasks"

    __table_args__ = (
        Index("ix_tasks_user_status", "user_id", "status"),
        Index("ix_tasks_user_due_date", "user_id", "due_date"),
        Index("ix_tasks_user_created_at", "user_id", "created_at"),
        Index("ix_tasks_user_category", "user_id", "category_id"),
        Index("ix_tasks_assigned_status", "assigned_to_id", "status"),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    status: Mapped[TaskStatus] = mapped_column(
        SQLEnum(
            TaskStatus,
            name="taskstatus",
        ),
        default=TaskStatus.PENDING,
        nullable=False,
        index=True,
    )

    priority: Mapped[TaskPriority] = mapped_column(
        SQLEnum(
            TaskPriority,
            name="taskpriority",
        ),
        default=TaskPriority.MEDIUM,
        nullable=False,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    assigned_to_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    due_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user: Mapped["User"] = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="tasks",
    )

    assignee: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[assigned_to_id],
        back_populates="assigned_tasks",
        lazy="selectin",
    )

    category: Mapped["Category | None"] = relationship(
        "Category",
        back_populates="tasks",
        lazy="selectin",
    )

    tags: Mapped[List["Tag"]] = relationship(
        "Tag",
        secondary=task_tags,
        back_populates="tasks",
        lazy="selectin",
    )

    comments: Mapped[List["TaskComment"]] = relationship(
        "TaskComment",
        back_populates="task",
        cascade="all, delete-orphan",
    )

    activities: Mapped[List["TaskActivity"]] = relationship(
        "TaskActivity",
        back_populates="task",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:

        return f"<Task id={self.id} title={self.title!r} status={self.status} user_id={self.user_id}>"