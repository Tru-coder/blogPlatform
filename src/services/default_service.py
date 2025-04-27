from abc import ABC
from typing import Any, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.database.session_manager import SessionManager
from src.domain.app_user import AppUser
from src.domain.comment import Comment
from src.domain.comment_reaction import CommentReaction
from src.domain.post import Post
from src.domain.tag import Tag
from src.domain.user_post_view import UserPostView
from src.exceptions.exceptions import DefaultNotFoundException
from src.repositories.comment_reaction_repository import CommentReactionRepository
from src.repositories.comment_repository import CommentRepository
from src.repositories.post_repository import PostRepository
from src.repositories.tag_repository import TagRepository
from src.repositories.user_post_view_repository import UserPostViewRepository
from src.repositories.user_repository import UserRepository
from src.utils.paginator import Paginator
from src.utils.time_interval import TimeInterval


class DefaultService[T_EntityClass:
                     (
                             AppUser,
                             Tag,
                             Comment,
                             Post,
                             CommentReaction,
                             UserPostView
                     ),

                     T_EntityRepository:
                     (
                             UserRepository,
                             TagRepository,
                             CommentRepository,
                             PostRepository,
                             CommentReactionRepository,
                            UserPostViewRepository
                     )](ABC):
    entity_not_found_exception = DefaultNotFoundException

    def __init__(self, entity_repository: T_EntityRepository):
        self.entity_repository = entity_repository

    @SessionManager.generate_async_transaction(session_kwarg_name="session")
    async def count_query_result_with_interval(
            self,
            session: AsyncSession,
            filters: dict[str, Any],
            time_interval: TimeInterval
    ) -> int:
        return await self.entity_repository.count_query_result_with_interval(
            session=session,
            filters=filters,
            time_interval=time_interval
        )

    async def create_entity(
            self,
            session: AsyncSession,
            entity: T_EntityClass
    ) -> T_EntityClass:
        entity = await self.entity_repository.add_one(
            session=session,
            entity=entity
        )
        return entity

    @SessionManager.generate_async_transaction(session_kwarg_name="session")
    async def get_one_with_filters(
            self,
            session: AsyncSession,
            filters: dict[str, Any]
    ) -> T_EntityClass:

        entity = await self.entity_repository.find_one_with_filters(
            session=session,
            filters=filters
        )

        if entity is None:
            raise self.entity_not_found_exception(
                f"Сущность <{self.entity_repository.entity_type.__name__}(filters={filters})> не найдена"
            )
        return entity

    @SessionManager.generate_async_transaction(session_kwarg_name="session")
    async def get_entity_by_id(
            self,
            session: AsyncSession,
            entity_id: int
    ) -> T_EntityClass:
        entity = await self.entity_repository.find_one_by_id(
            session=session,
            entity_id=entity_id
        )
        if entity is None:
            raise self.entity_not_found_exception(
                f"Сущность <{self.entity_repository.entity_type.__name__}(id={entity_id})> не найдена"
            )
        return entity

    @SessionManager.generate_async_transaction(session_kwarg_name="session")
    async def get_entity_by_uuid(
            self,
            session: AsyncSession,
            entity_uuid: UUID
    ) -> T_EntityClass:
        entity = await self.entity_repository.find_one_with_filters(
            session=session,
            filters={"uuid": entity_uuid}
        )
        if entity is None:
            raise self.entity_not_found_exception(
                f"Сущность <{self.entity_repository.entity_type.__name__}(uuid={entity_uuid})> не найдена"
            )
        return entity

    @SessionManager.generate_async_transaction(session_kwarg_name="session")
    async def get_entities(
            self,
            session: AsyncSession,
            paginator: Paginator,
    ) -> List[T_EntityClass]:
        entities = await self.entity_repository.find_all(
            session=session,
            paginator=paginator
        )
        return entities

    @SessionManager.generate_async_transaction(session_kwarg_name="session")
    async def get_entities_with_filters_and_interval(
            self,
            session: AsyncSession,
            filters: dict[str, Any],
            period: TimeInterval,
            paginator: Paginator,
    ) -> List[T_EntityClass]:
        return await self.entity_repository.find_all_with_filters_and_interval(
            session=session,
            filters=filters,
            time_interval=period,
            paginator=paginator
        )

    @SessionManager.generate_async_transaction(session_kwarg_name="session")
    async def get_all_entities(self, session: AsyncSession) -> List[T_EntityClass]:
        return await self.entity_repository.find_all(session=session, paginator=None)

    @staticmethod
    def update_entity(entity: T_EntityClass, new_values: dict[str, Any]) -> T_EntityClass:
        for key, value in new_values.items():
            setattr(entity, key, value)
        return entity

    @SessionManager.generate_async_transaction(session_kwarg_name="session")
    async def update_entity_by_id(
            self,
            session: AsyncSession,
            entity_id: int,
            new_values: dict[str, Any]) -> T_EntityClass:

        entity = await self.get_entity_by_id(session=session, entity_id=entity_id)
        entity = self.update_entity(entity=entity, new_values=new_values)

        # session.expire(entity, entity.updated_at)

        return entity

    async def create_entities(
            self,
            session: AsyncSession,
            entities: List[T_EntityClass]
    ) -> List[T_EntityClass]:
        entities = await self.entity_repository.add_many(
            session=session,
            entities=entities
        )
        return entities

    @SessionManager.generate_async_transaction(session_kwarg_name="session")
    async def delete_entity_by_uuid(self, session: AsyncSession, entity_uuid: UUID) -> None:
        await self.entity_repository.delete_all_data_with_filter(
            session=session,
            filters={'uuid': entity_uuid}
        )
