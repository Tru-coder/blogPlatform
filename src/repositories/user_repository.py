from src.domain.app_user import AppUser
from src.repositories.abstract.default_repository import DefaultRepository


class UserRepository(DefaultRepository[AppUser]):
    entity_type = AppUser
