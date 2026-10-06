from datetime import datetime, timezone
import enum
from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.activity import TaskActivity
    from app.models.category import Category
    from app.models.comment import TaskComment
    from app.models.notification import Notification
    from app.models.tag import Tag
    from app.models.task import Task


class UserRole(str, enum.Enum):
    CEO = "CEO"
    EMPLOYEE = "EMPLOYEE"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, name="userrole", native_enum=True),
        default=UserRole.EMPLOYEE,
        server_default=UserRole.EMPLOYEE.value,
        nullable=False,
        index=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    tasks: Mapped[List["Task"]] = relationship(
        "Task",
        foreign_keys="Task.user_id",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    assigned_tasks: Mapped[List["Task"]] = relationship(
        "Task",
        foreign_keys="Task.assigned_to_id",
        back_populates="assignee",
    )

    categories: Mapped[List["Category"]] = relationship(
        "Category",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    tags: Mapped[List["Tag"]] = relationship(
        "Tag",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    comments: Mapped[List["TaskComment"]] = relationship(
        "TaskComment",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    activities: Mapped[List["TaskActivity"]] = relationship(
        "TaskActivity",
        back_populates="user",
    )

    notifications: Mapped[List["Notification"]] = relationship(
        "Notification",
        back_populates="user",
        cascade="all, delete-orphan",
    )


    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} role={self.role.value} active={self.is_active}>"
