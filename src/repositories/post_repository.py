from datetime import datetime, timezone
from typing import List, Any
from uuid import UUID

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from src.domain.comment import Comment
from src.domain.comment_reaction import CommentReaction
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
            self, session: AsyncSession, post_uuid: UUID,  author_id: int
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
        conditional_sql_filters = self.entity_type.status == PostStatus.PUBLISHED
        if filters["author_id"] is not None:
            conditional_sql_filters = and_(
                conditional_sql_filters,
                self.entity_type.author_id == filters["author_id"]
            )
        if filters['tags']:
            subq = (
                select(PostTag.post_id)
                .filter(PostTag.tag_id.in_(filters['tags']))
            )
            conditional_sql_filters = and_(
                conditional_sql_filters,
                self.entity_type.id.in_(subq)
            )

        if filters['category'] is not None:
            conditional_sql_filters = and_(
                conditional_sql_filters,
                self.entity_type.category == filters['category']
            )
        if filters['content'] is not None:
            conditional_sql_filters = and_(
                conditional_sql_filters,
                self.entity_type.content.contains(filters['content'])
            )
        stmt = (
            select(self.entity_type)
            .filter(conditional_sql_filters)
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
        conditional_sql_filters = self.entity_type.status == PostStatus.PUBLISHED
        if filters["author_id"] is not None:
            conditional_sql_filters = and_(
                conditional_sql_filters,
                self.entity_type.author_id == filters["author_id"]
            )
        if filters['tags']:
            subq = (
                select(PostTag.post_id)
                .filter(PostTag.tag_id.in_(filters['tags']))
            )
            conditional_sql_filters = and_(
                conditional_sql_filters,
                self.entity_type.id.in_(subq)
            )

        if filters['category'] is not None:
            conditional_sql_filters = and_(
                conditional_sql_filters,
                self.entity_type.category == filters['category']
            )
        if filters['content'] is not None:
            conditional_sql_filters = and_(
                conditional_sql_filters,
                self.entity_type.content.contains(filters['content'])
            )

        stmt = (
            select(func.count(self.entity_type.id))
            .filter(conditional_sql_filters)
            .filter(self.entity_type.created_at.between(time_interval.start, time_interval.end))
            .select_from(self.entity_type)
        )
        return await session.scalar(stmt)

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

    async def find_post_with_comments_3(
            self,
            post_uuid: UUID,
            session: AsyncSession
    ) -> Post:
        # Подзапрос для подсчёта реакций (только количество)
        reaction_counts = (
            select(
                CommentReaction.comment_id,
                CommentReaction.reaction_type,
                func.count().label('count')
            )
            .group_by(CommentReaction.comment_id, CommentReaction.reaction_type)
            .subquery()
        )

        # Основной запрос для поста с комментариями
        query = (
            select(Post)
            .options(
                selectinload(Post.author),
                selectinload(Post.tags),
                selectinload(Post.comments).options(
                    selectinload(Comment.author),
                    selectinload(Comment.children).options(
                        selectinload(Comment.author)
                    )
                ),
            )
            .filter(Post.uuid == post_uuid)
        )

        result = await session.execute(query)
        post = result.scalars().first()

        # Дополнительно загружаем количество реакций
        if post and post.comments:
            comment_ids = [c.id for c in post.comments]
            reactions_query = select(reaction_counts).where(reaction_counts.c.comment_id.in_(comment_ids))
            reactions_result = await session.execute(reactions_query)
            reactions_data = reactions_result.all()

            # Создаем словарь {comment_id: {reaction_type: count}}
            reactions_dict = {}
            for comment_id, reaction_type, count in reactions_data:
                if comment_id not in reactions_dict:
                    reactions_dict[comment_id] = {}
                reactions_dict[comment_id][reaction_type] = count

            # Присваиваем данные о реакциях комментариям
            for comment in post.comments:
                comment.reactions_count = reactions_dict.get(comment.id, {})

        return post

    async def count_query_find_all(self, session: AsyncSession, filters: dict[str, Any]) -> int:
        stmt = (
            select(func.count(self.entity_type.id))
            .filter_by(**filters)
            .select_from(self.entity_type)
        )
        return await session.scalar(stmt)
