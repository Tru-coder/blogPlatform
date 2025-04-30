from typing import Any, List, Dict
from uuid import UUID

from sqlalchemy import select, func, true, false
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.domain.comment import Comment
from src.domain.comment_reaction import CommentReaction
from src.repositories.abstract.default_repository import DefaultRepository
from src.utils.paginator import Paginator


class CommentRepository(DefaultRepository[Comment]):
    entity_type = Comment

    async def find_comment_with_author(self, session: AsyncSession, comment_uuid: UUID) -> Comment | None:
        stmt = (
            select(self.entity_type)
            .filter(self.entity_type.uuid == comment_uuid)
            .options(
                joinedload(self.entity_type.author)
            )
        )

        res = await session.execute(stmt)
        return res.unique().scalar_one_or_none()

    async def get_comment_with_author_and_filters(
            self, session: AsyncSession, filters: dict[str, Any]) -> Comment | None:
        stmt = (
            select(self.entity_type)
            .filter_by(**filters)
            .options(
                joinedload(self.entity_type.author)
            )
        )

        res = await session.execute(stmt)
        return res.unique().scalar_one_or_none()

    async def find_root_comments_for_post(self, session: AsyncSession, post_id: int, paginator: Paginator) -> List[
        Comment]:
        stmt = (
            select(self.entity_type)
            .filter(
                self.entity_type.is_moderated == True,
                self.entity_type.post_id == post_id,
                self.entity_type.parent_id.is_(None)
            )
            .options(
                joinedload(self.entity_type.author),
            )
            .order_by(self.entity_type.created_at.desc())
            .offset(paginator.skip)
            .limit(paginator.limit)

        )
        res = await session.execute(stmt)
        return list(res.scalars().all())

    async def load_reactions_for_comments(
            self, session: AsyncSession, comment_ids: List[int]) -> Dict[int, Dict[str, int]]:
        # Подзапрос для подсчёта реакций
        reaction_counts = (
            select(
                CommentReaction.comment_id,
                CommentReaction.reaction_type,
                func.count().label('count')
            )
            .group_by(CommentReaction.comment_id, CommentReaction.reaction_type)
            .subquery()
        )

        reactions_query = (
            select(reaction_counts)
            .where(reaction_counts.c.comment_id.in_(comment_ids))
        )
        reactions_result = await session.execute(reactions_query)
        reactions_data = reactions_result.all()

        # Словарь реакций {comment_id: {reaction_type: count}}
        reactions_dict : dict[int, dict[str, int]] = {}
        for comment_id, reaction_type, count in reactions_data:
            if comment_id not in reactions_dict:
                reactions_dict[comment_id] = {}
            reactions_dict[comment_id][reaction_type] = count

        return reactions_dict

    async def find_children_comments(self, session: AsyncSession, parend_comment_id: int, paginator: Paginator) -> List[
        Comment]:
        stmt = (
            select(self.entity_type)
            .filter(self.entity_type.parent_id == parend_comment_id, self.entity_type.is_moderated == true())
            .options(
                joinedload(self.entity_type.author)
            )
            .order_by(self.entity_type.created_at.desc())
            .offset(paginator.skip)
            .limit(paginator.limit)

        )

        res = await session.execute(stmt)
        return list(res.unique().scalars())

    async def count_comments_query(self, session: AsyncSession, filters: dict[str, Any]) -> int:
        stmt = (
            select(func.count(self.entity_type.id))
            .filter_by(**filters)
            .select_from(self.entity_type)
        )
        return await session.scalar(stmt)

    async def find_to_moderate_comments(self, session: AsyncSession, paginator:Paginator) -> List[Comment]:
        stmt = (
            select(self.entity_type)
            .filter(self.entity_type.is_moderated == false())
            .options(
                joinedload(self.entity_type.author)
            )
            .order_by(self.entity_type.created_at.desc())
            .offset(paginator.skip)
            .limit(paginator.limit)
        )

        res = await session.execute(stmt)
        return list(res.scalars().all())
