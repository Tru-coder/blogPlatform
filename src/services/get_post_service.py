from src.domain.post import Post
from src.repositories.post_repository import PostRepository
from src.services.default_service import DefaultService


class GetPostService(DefaultService[Post, PostRepository]):

    def __init__(self, entity_repository: PostRepository):
        super().__init__(entity_repository)

    async def create_entity(self, *args, **kwargs):
        raise NotImplementedError

    async def update_entity(self, *args, **kwargs):
        raise NotImplementedError

    async def update_entity_by_id(self, *args, **kwargs):
        raise NotImplementedError

    async def create_entities(self, *args, **kwargs):
        raise NotImplementedError

    async def delete_entity_by_uuid(self, *args, **kwargs):
        raise NotImplementedError
