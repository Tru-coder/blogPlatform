from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.domain.abstract.base_entity import BaseEntity


class PostTag(BaseEntity):
    __tablename__ = "post_tag"

    post_id: Mapped[int] = mapped_column(
        ForeignKey("post.id", ondelete="CASCADE"),
        nullable=False
    )
    tag_id: Mapped[int] = mapped_column(
        ForeignKey("tag.id", ondelete="CASCADE"),
        nullable=False
    )

    __table_args__ = (UniqueConstraint("post_id", "tag_id", name="unique_post_tag"),)