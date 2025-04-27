import enum
from typing import TYPE_CHECKING, List

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.auth.permission import Permission
from src.domain.abstract.base_entity import BaseEntity

if TYPE_CHECKING:
    from src.domain.post import Post
    from src.domain.comment import Comment
    from src.domain.comment_reaction import CommentReaction
    from src.domain.user_post_view import UserPostView

@enum.unique
class Role(enum.Enum):
    ADMIN = Permission.admin_permissions()
    USER = Permission.user_permissions()
    AUTHOR = Permission.author_permissions()

    def __str__(self):
        return self.name.lower()

    @classmethod
    def all_values(cls):
        return [role.value for role in cls]


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