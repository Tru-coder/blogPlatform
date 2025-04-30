from typing import List, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.database.session_manager import SessionManager
from src.domain.app_user import AppUser
from src.domain.comment import Comment
from src.domain.comment_reaction import CommentReaction
from src.domain.enums.enums import AllowedReactionType
from src.exceptions.exceptions import DefaultNotFoundException
from src.repositories.comment_reaction_repository import CommentReactionRepository
from src.services.comment_service import CommentService
from src.services.default_service import DefaultService
from src.utils.paginator import Paginator


class CommentReactionService(DefaultService[CommentReaction, CommentReactionRepository]):
    entity_not_found_exception = DefaultNotFoundException

    def __init__(self, entity_repository: CommentReactionRepository, comment_service: CommentService) -> None:
        super().__init__(entity_repository)
        self.comment_service = comment_service

    @SessionManager.generate_async_transaction(session_kwarg_name="session")
    async def put_reaction(
            self, session: AsyncSession, comment_uuid: UUID, reaction: AllowedReactionType, current_user: AppUser
    ) -> CommentReaction:
        comment = await self.comment_service.get_comment_with_author_and_filters(
            session=session, filters={Comment.uuid.key: comment_uuid, Comment.is_moderated.key: True}
        )

        existed_reaction = await self.entity_repository.find_one_with_filters(
            session=session,
            filters={
                CommentReaction.comment_id.key: comment.id, CommentReaction.user_id.key: current_user.id
            }
        )

        if existed_reaction is None:
            reaction_entity = CommentReaction(reaction_type=reaction.value, comment_id=comment.id, user_id=current_user.id)
            return await self.create_entity(session=session, entity=reaction_entity)

        existed_reaction.reaction_type = reaction.value
        return existed_reaction

    @SessionManager.generate_async_transaction(session_kwarg_name="session")
    async def delete_reaction(self, session: AsyncSession, reaction_uuid: UUID, current_user: AppUser) -> None:
        existed_reaction = await self.get_one_with_filters(
            session=session,
            filters={CommentReaction.uuid.key: reaction_uuid, CommentReaction.user_id.key: current_user.id}
        )

        if existed_reaction is None:
            raise self.entity_not_found_exception(f"Реакция с uuid {reaction_uuid} и c автором {current_user!r} не найдена")

        await self.delete_entity_by_uuid(session=session, entity_uuid=existed_reaction.uuid)

    @SessionManager.generate_async_transaction(session_kwarg_name="session")
    async def get_my_reactions(self, session: AsyncSession, current_user: AppUser, paginator: Paginator) -> Tuple[List[CommentReaction], int]:
        reactions =  await self.entity_repository.find_reactions_with_relations(session=session, filters={CommentReaction.user_id.key: current_user.id}, paginator=paginator)
        total_count =  await self.entity_repository.count_reactions_query(session=session, filters={CommentReaction.user_id.key: current_user.id})

        return reactions, total_count