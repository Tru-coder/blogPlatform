from abc import ABC
from typing import List, Any, Type

from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.abstract.base_entity import BaseEntity
from src.repositories.abstract.abstract_repository import AbstractRepository
from src.utils.paginator import Paginator
from src.utils.time_interval import TimeInterval


class DefaultRepository[T:BaseEntity](AbstractRepository, ABC):
    entity_type = Type[T]

    async def find_all_with_filters_and_interval(
            self,
            session: AsyncSession,
            filters: dict[str, Any],
            time_interval: TimeInterval,
            paginator: Paginator) -> List[T]:
        stmt = (
            select(self.entity_type)
            .filter(
                self.entity_type.created_at.between(time_interval.start, time_interval.end)
            )
            .filter_by(**filters)
            .order_by(self.entity_type.created_at.desc())
            .offset(paginator.skip)
            .limit(paginator.limit)
        )
        res = await session.execute(stmt)
        return list(res.scalars().all())

    async def find_all_with_filters(
            self,
            session: AsyncSession,
            filters: dict[str, Any],
            paginator: Paginator) -> List[T]:
        stmt = (
            select(self.entity_type)
            .filter_by(**filters)
            .order_by(self.entity_type.created_at.desc())
            .offset(paginator.skip)
            .limit(paginator.limit)
        )
        res = await session.execute(stmt)
        return list(res.scalars().all())

    async def find_all(
            self,
            session: AsyncSession,
            paginator: Paginator | None = None
    ) -> List[T]:
        stmt = (
            select(self.entity_type)
            .order_by(self.entity_type.created_at.desc())
        )
        if paginator:
            stmt = stmt.offset(paginator.skip).limit(paginator.limit)
        res = await session.execute(stmt)
        return list(res.scalars().all())

    async def find_one_by_id(
            self, session: AsyncSession, entity_id: int) -> T | None:
        stmt = (
            select(self.entity_type)
            .filter(self.entity_type.id == entity_id)
        )
        res = await session.execute(stmt)
        return res.scalar_one_or_none()

    async def find_one_with_filters(
            self,
            session: AsyncSession,
            filters: dict[str, Any]) -> T | None:
        stmt = (
            select(self.entity_type)
            .filter_by(**filters)
        )
        res = await session.execute(stmt)
        return res.scalar_one_or_none()

    async def add_one(
            self,
            session: AsyncSession,
            entity: T
    ) -> T:
        session.add(entity)
        await session.flush()
        return entity

    async def add_many(
            self,
            session: AsyncSession,
            entities: List[T]
    ) -> List[T]:
        session.add_all(entities)
        await session.flush()
        return entities

    async def delete_all_data_in_table(
            self,
            session: AsyncSession
    ) -> None:
        stmt = delete(self.entity_type)
        await session.execute(stmt)

    async def delete_all_data_with_filter(
            self,
            session: AsyncSession,
            filters: dict[str, Any]
    ) -> None:
        stmt = (
            delete(self.entity_type)
            .filter_by(**filters)
        )
        await session.execute(stmt)

    async def count_query_result_with_interval(
            self,
            session: AsyncSession,
            filters: dict[str, Any],
            time_interval: TimeInterval
    ) -> int:
        stmt = (
            select(func.count(self.entity_type.id))
            .filter(
                self.entity_type.created_at.between(
                    time_interval.start,
                    time_interval.end
                )
            )
            .filter_by(**filters)
            .select_from(self.entity_type)
        )
        return await session.scalar(stmt)
