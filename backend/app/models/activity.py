from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.task import Task
    from app.models.user import User


class TaskActivity(Base):
    __tablename__ = "task_activities"

    __table_args__ = (
        Index("ix_task_activities_task_id", "task_id"),
        Index("ix_task_activities_user_id", "user_id"),
        Index("ix_task_activities_created_at", "created_at"),
        Index("ix_task_activities_task_created", "task_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    task_id: Mapped[int] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
    )

    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    action: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    task: Mapped["Task"] = relationship(
        "Task",
        back_populates="activities",
    )

    user: Mapped["User | None"] = relationship(
        "User",
        back_populates="activities",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<TaskActivity id={self.id} task_id={self.task_id} action={self.action!r}>"
