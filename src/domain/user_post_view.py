from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.domain.abstract.base_entity import BaseEntity


class UserPostView(BaseEntity):
    __tablename__ = "user_post_view"

    user_id: Mapped[int] = mapped_column(ForeignKey("app_user.id", ondelete="CASCADE"), nullable=False)
    post_id: Mapped[int] = mapped_column(ForeignKey("post.id", ondelete="CASCADE"), nullable=False)

    __table_args__ = (UniqueConstraint("user_id", "post_id", name="unique_user_post_view"),)
