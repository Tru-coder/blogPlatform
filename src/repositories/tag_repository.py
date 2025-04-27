from src.domain.tag import Tag
from src.repositories.abstract.default_repository import DefaultRepository


class TagRepository(DefaultRepository):
    entity_type = Tag