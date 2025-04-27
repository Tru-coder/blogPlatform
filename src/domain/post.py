import enum
from datetime import datetime
from typing import TYPE_CHECKING, List, TypedDict
from uuid import UUID

from sqlalchemy import String, ForeignKey, DateTime, Integer
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.domain.abstract.base_entity import BaseEntity

if TYPE_CHECKING:
    from src.domain.app_user import AppUser
    from src.domain.tag import Tag
    from src.domain.comment import Comment


@enum.unique
class PostStatus(enum.Enum):
    DRAFT = "черновик"
    PUBLISHED = "опубликован"
    ARCHIVED = "заархивирован"

    @classmethod
    def all_values(cls):
        return [role.value for role in cls]


class Post(BaseEntity):
    __tablename__ = "post"

    title: Mapped[str] = mapped_column(
        String(64),
        nullable=False
    )

    content: Mapped[str] = mapped_column(
        String,
        nullable=False
    )

    category: Mapped[str] = mapped_column(
        String(64),
        nullable=False
    )

    status: Mapped[PostStatus] = mapped_column(
        ENUM(PostStatus, name="status"),
        nullable=False
    )

    author_id: Mapped[int] = mapped_column(
        ForeignKey("app_user.id", ondelete="CASCADE"),
        nullable=False
    )

    views: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="Количество просмотров от зарегистрированных пользователей, обновляется автоматически scheduler-ом "
    )

    to_published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        name="to_published_at",
        nullable=True
    )

    author: Mapped['AppUser'] = relationship(
        back_populates="posts"
    )

    tags: Mapped[List["Tag"]] = relationship(
        secondary="post_tag",
        back_populates="posts"
    )

    comments: Mapped[List["Comment"]] = relationship(
        back_populates="post"
    )

    viewed_by: Mapped[List["AppUser"]] = relationship(
        secondary="user_post_view",
        back_populates="viewed_posts"
    )


class PostFiltersUsersParams(TypedDict):
    tags: List[str] | None
    category: str | None
    content: str | None
    author_uuid: UUID | None


class PostFiltersParams(TypedDict):
    tags: List[int] | None
    category: str | None
    author_id: int | None
    content: str | None
