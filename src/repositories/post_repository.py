from datetime import datetime, timezone
from typing import List, Any
from uuid import UUID

from sqlalchemy import select, and_, func, ColumnElement
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from src.domain.enums.enums import PostStatus
from src.domain.post import Post, PostFiltersParams
from src.domain.post_tag import PostTag
from src.redis_tools.redis_tools import RedisTools
from src.repositories.abstract.default_repository import DefaultRepository
from src.utils.paginator import Paginator
from src.utils.time_interval import TimeInterval


class PostRepository(DefaultRepository[Post]):
    entity_type = Post

    async def find_post_with_tags_and_author(
            self, session: AsyncSession, post_uuid: UUID, author_id: int
    ) -> Post | None:
        stmt = (
            select(self.entity_type)
            .filter(self.entity_type.uuid == post_uuid, self.entity_type.author_id == author_id)
            .options(
                joinedload(self.entity_type.tags)
            )
        )

        res = await session.execute(stmt)
        return res.unique().scalar_one_or_none()

    @RedisTools.cache_find_published_posts(60)
    async def find_published_posts(
            self, session: AsyncSession, paginator: Paginator, time_interval: TimeInterval, filters: PostFiltersParams
    ) -> List[Post]:
        conditional_filters = self._build_published_posts_filters(filters)

        stmt = (
            select(self.entity_type)
            .filter(conditional_filters)
            .filter(self.entity_type.created_at.between(time_interval.start, time_interval.end))
            .order_by(self.entity_type.created_at.desc())
            .offset(paginator.skip)
            .limit(paginator.limit)
        )
        res = await session.execute(stmt)
        return list(res.scalars().all())

    async def count_query_find_published_posts(
            self, session: AsyncSession, filters: PostFiltersParams, time_interval: TimeInterval
    ) -> int:
        conditional_filters = self._build_published_posts_filters(filters)

        stmt = (
            select(func.count(self.entity_type.id))
            .filter(conditional_filters)
            .filter(self.entity_type.created_at.between(time_interval.start, time_interval.end))
            .select_from(self.entity_type)
        )
        return await session.scalar(stmt) or 0

    def _build_published_posts_filters(
            self,
            filters: PostFiltersParams
    ) -> ColumnElement[bool]:
        conditional_filters = self.entity_type.status == PostStatus.PUBLISHED

        if filters["author_id"] is not None:
            conditional_filters = and_(
                conditional_filters,
                self.entity_type.author_id == filters["author_id"]
            )

        if filters['tags']:
            subq = (
                select(PostTag.post_id)
                .filter(PostTag.tag_id.in_(filters['tags']))
            )
            conditional_filters = and_(
                conditional_filters,
                self.entity_type.id.in_(subq)
            )

        if filters['category'] is not None:
            conditional_filters = and_(
                conditional_filters,
                self.entity_type.category == filters['category']
            )

        if filters['content'] is not None:
            conditional_filters = and_(
                conditional_filters,
                self.entity_type.content.contains(filters['content'])
            )

        return conditional_filters

    async def find_posts_to_publish(self, session: AsyncSession) -> List[Post]:
        stmt = (
            select(self.entity_type)
            .filter(self.entity_type.status == PostStatus.DRAFT,
                    self.entity_type.to_published_at <= datetime.now(tz=timezone.utc)
                    )
        )
        res = await  session.execute(stmt)
        return list(res.scalars())

    async def find_post_with_author_and_tags(
            self,
            post_uuid: UUID,
            session: AsyncSession
    ) -> Post | None:
        stmt = (
            select(self.entity_type)
            .filter(self.entity_type.uuid == post_uuid)
            .options(
                selectinload(self.entity_type.author),
                selectinload(self.entity_type.tags),
            )
        )

        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def count_query_find_all(self, session: AsyncSession, filters: dict[str, Any]) -> int:
        stmt = (
            select(func.count(self.entity_type.id))
            .filter_by(**filters)
            .select_from(self.entity_type)
        )
        return await session.scalar(stmt) or 0
