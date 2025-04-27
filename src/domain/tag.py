from typing import List, TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.domain.abstract.base_entity import BaseEntity

if TYPE_CHECKING:
    from src.domain.post import Post

class Tag(BaseEntity):
    __tablename__ = "tag"

    name: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False
    )

    posts: Mapped[List["Post"]] = relationship(
        secondary="post_tag",
        back_populates="tags"
    )