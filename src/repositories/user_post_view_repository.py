from typing import Any, TypedDict, List

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.domain.post import Post
from src.domain.user_post_view import UserPostView
from src.repositories.abstract.default_repository import DefaultRepository
from src.utils.paginator import Paginator
from src.utils.time_interval import TimeInterval


class ViewPerPostModel(TypedDict):
    tag_id: int
    views_count: int

class UserPostViewRepository(DefaultRepository[UserPostView]):
    entity_type = UserPostView

    async def find_view_by_user_id_and_post_id(
            self, session: AsyncSession, user_id: int, post_id: int
    ) -> UserPostView | None:
        return await self.find_one_with_filters(
            session=session,
            filters={self.entity_type.user_id.key: user_id, self.entity_type.post_id.key: post_id}
        )


    async def update_views_count_on_posts(self, session: AsyncSession) -> None:
        views_subquery  = (
            select(self.entity_type.post_id, func.count().label("views_count"))
            .group_by(UserPostView.post_id)
            .subquery()
        )
        update_stmt = (
            update(Post)
            .values(views=views_subquery.c.views_count)
            .where(Post.id == views_subquery.c.post_id)
        )
        await session.execute(update_stmt)

    async def count_query_result(
            self,
            session: AsyncSession,
            filters: dict[str, Any],
    ) -> int:
        stmt = (
            select(func.count(self.entity_type.id))
            .filter_by(**filters)
            .select_from(self.entity_type)
        )
        return await session.scalar(stmt)

    async def find_all_viewed_posts(self, session: AsyncSession, user_id: int, paginator: Paginator) -> List[Post]:
        stmt = (
            select(Post)
            .join(UserPostView, UserPostView.post_id == Post.id)
            .filter(UserPostView.user_id == user_id)
            # .options(joinedload(Post.author))
            .order_by(UserPostView.created_at.desc())
            .offset(paginator.skip)
            .limit(paginator.limit)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())