from typing import TYPE_CHECKING

from sqlalchemy import Unicode, ForeignKey, UniqueConstraint
from sqlalchemy.orm import mapped_column, Mapped, relationship

from src.domain.abstract.base_entity import BaseEntity

if TYPE_CHECKING:
    from src.domain.app_user import AppUser
    from src.domain.comment import Comment


class CommentReaction(BaseEntity):
    __tablename__ = "comment_reaction"

    reaction_type: Mapped[str] = mapped_column(
        Unicode(10),
        nullable=False
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("app_user.id", ondelete="CASCADE"),
        nullable=False
    )
    comment_id: Mapped[int] = mapped_column(
        ForeignKey("comment.id", ondelete="CASCADE"),
        nullable=False
    )

    __table_args__ = (
        UniqueConstraint("user_id", "comment_id", name="unique_comment_reaction"),
    )

    user: Mapped["AppUser"] = relationship(back_populates="comment_reactions")
    comment: Mapped["Comment"] = relationship(back_populates="comment_reactions")
