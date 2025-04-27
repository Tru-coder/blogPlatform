from uuid import UUID

from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.security_utils import SecurityUtils
from src.database.session_manager import SessionManager
from src.domain.app_user import AppUser
from src.exceptions.user_exceptions import UserNotFoundException, UserAlreadyExistsException
from src.http_schemas.user_schemas import UserRegisterSchema
from src.repositories.user_repository import UserRepository
from src.services.default_service import DefaultService


class UserService(DefaultService[AppUser, UserRepository]):
    entity_not_found_exception = UserNotFoundException

    def __init__(self, entity_repository: UserRepository):
        super().__init__(entity_repository=entity_repository)

    @SessionManager.generate_async_transaction(session_kwarg_name="session")
    async def user_register(self, session: AsyncSession, request_body: UserRegisterSchema) -> AppUser:
        await self.check_on_existence(session=session, login=request_body.login)

        user = AppUser(**request_body.model_dump(exclude={'role_value'}))
        user.password = SecurityUtils.hash_password(user)
        return await self.create_entity(
            session=session,
            entity=user
        )

    async def check_on_existence(self, session: AsyncSession, login: str | EmailStr) -> None:
        existed_user = await self.entity_repository.find_one_with_filters(
            session=session,
            filters={AppUser.login.key: login}
        )
        if existed_user is not None:
            raise UserAlreadyExistsException(f"Пользователь с логином {login} уже существует")

    @SessionManager.generate_async_transaction(session_kwarg_name="session")
    async def update_password(self, session: AsyncSession, user_uuid: UUID,
                              request_body: UserRegisterSchema) -> AppUser:
        user = await self.get_entity_by_uuid(session=session, entity_uuid=user_uuid)

        user.password = request_body.password
        user.password = SecurityUtils.hash_password(user)
        user = self.update_entity(entity=user, new_values=request_body.model_dump())
        return user
