from datetime import datetime
from typing import Any, List
from uuid import UUID as PYUUID

from sqlalchemy import DateTime, Integer, func, UUID, text
from sqlalchemy.orm import mapped_column, Mapped

from src.database.app_database import Base


class BaseEntity(Base):
    __abstract__ = True
    id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        unique=True,
        primary_key=True,
        autoincrement=True
    )
    uuid: Mapped[PYUUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        unique=True,
        server_default=text("gen_random_uuid()")
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now(),
        nullable=True
    )

    # Define metadata attribute
    __table_args__ = {"extend_existing": True}

    def __repr__(self) -> str:
        return "<{0.__class__.__name__}(id={0.id!r})>".format(self)

    def to_dict(self, exclude_keys: List[str] = None) -> dict[str, Any]:
        exclude_keys = exclude_keys or []
        return {
            attr: getattr(self, attr)
            for attr in self.__dict__
            if not attr.startswith("_") and attr not in exclude_keys
        }
