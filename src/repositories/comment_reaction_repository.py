from typing import List, Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.domain.comment import Comment
from src.domain.comment_reaction import CommentReaction
from src.repositories.abstract.default_repository import DefaultRepository
from src.utils.paginator import Paginator


class CommentReactionRepository(DefaultRepository[CommentReaction]):
    entity_type = CommentReaction

    async def find_reactions_with_relations(self, session: AsyncSession, filters: dict[str, Any],
                                            paginator: Paginator) -> List[CommentReaction]:
        stmt = (
            select(self.entity_type)
            .filter_by(**filters)
            .options(joinedload(CommentReaction.comment).joinedload(Comment.author))
            .order_by(self.entity_type.created_at.desc())
            .offset(paginator.skip)
            .limit(paginator.limit)
        )
        res = await session.execute(stmt)
        return list(res.scalars().all())

    async def count_reactions_query(self, session: AsyncSession, filters: dict[str, Any]) -> int:
        stmt = (
            select(func.count(self.entity_type.id))
            .filter_by(**filters)
            .select_from(self.entity_type)
        )
        return await session.scalar(stmt)
