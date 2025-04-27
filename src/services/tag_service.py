from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.database.session_manager import SessionManager
from src.domain.tag import Tag
from src.exceptions.tag_exceptions import TagNotFoundException, TagAlreadyExistsException
from src.http_schemas.tag_schema import CreateTagSchema, UpdateTagSchema
from src.repositories.tag_repository import TagRepository
from src.services.default_service import DefaultService


class TagService(DefaultService[Tag, TagRepository]):
    entity_not_found_exception = TagNotFoundException

    def __init__(self, entity_repository: TagRepository):
        super().__init__(entity_repository)

    @SessionManager.generate_async_transaction(session_kwarg_name="session")
    async def create_tag(self, session: AsyncSession, request_body: CreateTagSchema) -> Tag:
        existed_tag = await self.entity_repository.find_one_with_filters(
            session=session,
            filters={Tag.name.key: request_body.name}
        )
        if existed_tag is not None:
            raise TagAlreadyExistsException(f"Тег с именем {request_body.name} уже существует")

        return await self.create_entity(
            session=session,
            entity=Tag(**request_body.model_dump())
        )

    @SessionManager.generate_async_transaction(session_kwarg_name="session")
    async def update_tag(self, session: AsyncSession, tag_uuid: UUID, request_body: UpdateTagSchema) -> Tag:
        existed_tag = await self.entity_repository.find_one_with_filters(
            session=session,
            filters={Tag.name.key: request_body.name}
        )
        if existed_tag is not None and existed_tag.uuid != tag_uuid:
            raise self.entity_not_found_exception(f"Тег с именем {request_body.name} уже существует")

        return self.update_entity(
            entity=await self.get_entity_by_uuid(session=session, entity_uuid=tag_uuid),
            new_values=request_body.model_dump()
        )

    async def get_tag_by_name(self, session: AsyncSession, name: str) -> Tag:
        existed_tag = await self.entity_repository.find_one_with_filters(
            session=session,
            filters={Tag.name.key: name}
        )
        if existed_tag is None:
            raise  self.entity_not_found_exception(f"Тег с именем {name} не найден")

        return existed_tag