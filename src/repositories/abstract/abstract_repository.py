from abc import ABC, abstractmethod
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from src.utils.paginator import Paginator


class AbstractRepository[T](ABC):
    not_implemented_error_message = "Subclasses must implement this method"

    @abstractmethod
    async def find_all(
            self,
            session: AsyncSession,
            paginator: Paginator
    ) -> List[T]:
        raise NotImplementedError(self.not_implemented_error_message)

    @abstractmethod
    async def find_one_by_id(
            self,
            session: AsyncSession,
            entity_id: int
    ) -> T:
        raise NotImplementedError(self.not_implemented_error_message)

    @abstractmethod
    async def add_one(
            self,
            session: AsyncSession,
            entity: T
    ) -> T:
        raise NotImplementedError(self.not_implemented_error_message)

    @abstractmethod
    async def add_many(
            self,
            session: AsyncSession,
            entities: List[T]
    ) -> List[T]:
        raise NotImplementedError(self.not_implemented_error_message)
