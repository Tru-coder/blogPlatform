from typing import TYPE_CHECKING, List

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.domain.abstract.base_entity import BaseEntity
from src.domain.enums.enums import Role

if TYPE_CHECKING:
    from src.domain.post import Post
    from src.domain.comment import Comment
    from src.domain.comment_reaction import CommentReaction


class AppUser(BaseEntity):
    __tablename__ = "app_user"

    login: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True
    )

    role: Mapped[Role] = mapped_column(
        ENUM(Role, name="role"),
        nullable=False,
        default=Role.ADMIN
    )

    password: Mapped[str | None] = mapped_column(
        String,
        name="password",
        nullable=True,
        comment="Пароль"
    )

    posts: Mapped[List["Post"]] = relationship(
        back_populates="author"
    )

    comments: Mapped[List["Comment"]] = relationship(
        back_populates="author"
    )

    comment_reactions: Mapped[List["CommentReaction"]] = relationship(
        back_populates="user"
    )

    viewed_posts: Mapped[List["Post"]] = relationship(
        secondary="user_post_view",
        back_populates="viewed_by"
    )

    def __repr__(self):
        return f"<AppUser(login={self.login!r}, role={self.role_repr})>"

    @property
    def role_repr(self) -> str:
        return self.role.name

    @property
    def get_permissions(self) -> List[str]:
        return [permission.value for permission in self.role.value]