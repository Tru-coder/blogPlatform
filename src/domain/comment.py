from typing import TYPE_CHECKING, List

from sqlalchemy import ForeignKey, String, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.domain.abstract.base_entity import BaseEntity

if TYPE_CHECKING:
    from src.domain.app_user import AppUser
    from src.domain.post import Post
    from src.domain.comment_reaction import CommentReaction


class Comment(BaseEntity):
    __tablename__ = "comment"

    # requires to be duplicated due to self-reference
    id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        unique=True,
        primary_key=True,
        autoincrement=True
    )
    post_id: Mapped[int] = mapped_column(
        ForeignKey("post.id", ondelete="CASCADE"), nullable=False
    )

    author_id: Mapped[int] = mapped_column(
        ForeignKey("app_user.id", ondelete="CASCADE"), nullable=False
    )

    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("comment.id", ondelete="CASCADE"), nullable=True
    )

    is_moderated: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False
    )

    content: Mapped[str] = mapped_column(
        String(512),
        nullable=False
    )

    children = relationship("Comment", back_populates="parent")

    # https://docs.sqlalchemy.org/en/20/orm/self_referential.html
    parent = relationship("Comment", back_populates="children", remote_side=[id])

    post: Mapped["Post"] = relationship(
        back_populates="comments"
    )

    author: Mapped["AppUser"] = relationship(
        back_populates="comments"
    )

    comment_reactions: Mapped[List["CommentReaction"]] = relationship(back_populates="comment")
