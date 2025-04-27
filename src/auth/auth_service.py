from dataclasses import dataclass
from datetime import datetime
from functools import wraps
from typing import Callable, Coroutine, Any, TypeVar, ParamSpec, Annotated, Tuple

import jwt
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError
from fastapi import HTTPException, status, Cookie
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.jwt_service import JWTService, RefreshToken, TokenType
from src.auth.security_utils import SecurityUtils
from src.database.session_manager import SessionManager
from src.domain.app_user import AppUser
from src.http_schemas.auth_schema import UserLogin
from src.exceptions.user_exceptions import UserNotFoundException
from src.logger.app_logger import AppLogger
from src.repositories.user_repository import UserRepository

P = ParamSpec("P")
T = TypeVar("T")


@dataclass
class UserTokens:
    access_token: str
    access_token_expired_at: datetime
    refresh_token: str
    refresh_token_expired_at: datetime


class AuthService:
    unauthorized_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    @staticmethod
    def handle_login_exceptions(func: Callable[P, Coroutine[Any, Any, T]]) -> Callable[P, Coroutine[Any, Any, T]]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            try:
                return await func(*args, **kwargs)
            except (
                    UserNotFoundException,
                    VerifyMismatchError,
                    VerificationError,
                    InvalidHashError,
            ):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        return wrapper

    @staticmethod
    def handle_token_exceptions(func: Callable[P, Coroutine[Any, Any, T]]) -> Callable[P, Coroutine[Any, Any, T]]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            token = kwargs.get("token")
            try:
                return await func(*args, **kwargs)
            except jwt.ExpiredSignatureError as e:
                AppLogger.custom_logger.warning(msg=f"Токен={token} доступа истёк", exc_info=e)
                raise AuthService.unauthorized_exception

            except jwt.PyJWTError as e:
                AppLogger.custom_logger.exception(msg=f"Ошибка при декодировании токена={token}", exc_info=e)
                raise AuthService.unauthorized_exception

        return wrapper

    @staticmethod
    async def generate_user_tokens(user: AppUser) -> UserTokens:

        access_token_payload = {"sub": user.login}
        access_token = JWTService.generate_access_token(payload=access_token_payload)

        refresh_payload = {"sub": user.login}
        refresh_token = JWTService.generate_refresh_token(payload=refresh_payload)

        await JWTService.save_refresh_token(
            refresh_token=RefreshToken(
                jti=refresh_payload["jti"],
                created_at=refresh_payload["iat"],
                expired_at=refresh_payload["exp"],
                subject=refresh_payload["sub"],
                revoked=False
            )
        )

        return UserTokens(
            access_token=access_token,
            access_token_expired_at=access_token_payload["exp"],
            refresh_token=refresh_token,
            refresh_token_expired_at=refresh_payload["exp"],
        )

    @SessionManager.generate_async_transaction(session_kwarg_name="session")
    @handle_login_exceptions
    async def get_user_by_login_form(self, session: AsyncSession, request_body: UserLogin) -> AppUser:
        user = await self.user_repository.find_one_with_filters(
            session=session,
            filters={AppUser.login.key: request_body.login}
        )
        if user is None:
            raise UserNotFoundException(f'Пользователь(login={request_body.login}) не найден')

        if SecurityUtils.check_password(
                user=user,
                password_from_db=user.password,
                password_from_request=request_body.password
        ) and SecurityUtils.ph.check_needs_rehash(user.password):
            user.password = SecurityUtils.rehash_user_password(
                user=user,
                user_password=request_body.password
            )

        return user

    async def login_user(self, request_body: UserLogin) -> UserTokens:
        user = await self.get_user_by_login_form(request_body=request_body)

        AppLogger.custom_logger.info(f"User = {user!r} login успешен. Генерерируем токены....")
        return await self.generate_user_tokens(user=user)

    @handle_token_exceptions
    async def get_current_user(self, token: Annotated[str | None, Cookie(alias="access_token")] = None) -> AppUser:
        if token is None:
            raise self.unauthorized_exception

        payload = JWTService.decode_jwt(jwt_token=token)

        if payload["token_type"] != TokenType.ACCESS.value:
            AppLogger.custom_logger.error(
                msg=f"Пользователь(логин={payload['sub']}) предоставил неверный тип токена: {payload['token_type']}."
                    f"Подозрительная активность"
            )
            raise self.unauthorized_exception

        try:
            user = await self.get_user_by_login(user_login=payload["sub"])
        except UserNotFoundException:
            raise self.unauthorized_exception

        return user

    async def get_optional_current_user(
            self, token: Annotated[str | None, Cookie(alias="access_token")] = None
    ) -> AppUser | None:
        if token is None:
            return None
        try:
            return await self.get_current_user(token=token)
        except HTTPException:
            return None

    @SessionManager.generate_async_transaction(session_kwarg_name="session")
    async def get_user_by_login(self, session: AsyncSession, user_login: str) -> AppUser:
        user = await self.user_repository.find_one_with_filters(
            session=session,
            filters={AppUser.login.key: user_login}
        )
        if not user:
            raise UserNotFoundException(f"<Пользователь(login={user_login})> не найден")

        return user

    @staticmethod
    @handle_token_exceptions
    async def refresh_user_tokens(
            token: str
    ) -> Tuple[str, datetime]:

        refresh_token_payload = JWTService.decode_jwt(jwt_token=token)
        user_refresh_token = await JWTService.get_user_token_by_jti(jti=refresh_token_payload["jti"])

        if refresh_token_payload["token_type"] != TokenType.REFRESH.value:
            AppLogger.custom_logger.error(
                msg=f"Пользователь(login={refresh_token_payload['sub']}) неверный тип токена: {refresh_token_payload['token_type']}."
                    f" Подозрительная активность. Доступ запрещен")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

        if user_refresh_token.revoked:
            AppLogger.custom_logger.error(
                msg=f"Refresh токен отозван. Token={token}. Доступ запрещен"
            )
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

        access_token_payload = {"sub": refresh_token_payload["sub"]}
        access_token = JWTService.generate_access_token(access_token_payload)

        return access_token, access_token_payload["exp"]

    @staticmethod
    @handle_token_exceptions
    async def logout(refresh_token: str) -> None:
        payload = JWTService.decode_jwt(jwt_token=refresh_token)
        user_refresh_token = await JWTService.get_user_token_by_jti(jti=payload["jti"])

        if user_refresh_token.revoked:
            AppLogger.custom_logger.error(
                msg=f"Refresh токен отозван. Token={refresh_token}. Logout операция отменена"
            )
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

        if payload["token_type"] != TokenType.REFRESH.value:
            AppLogger.custom_logger.error(
                msg=f"Пользователь(login={payload['sub']}) неверный тип токена: {payload['token_type']}."
                    f"Подозрительная активность"
            )
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

        user_refresh_token.revoked = True
        await JWTService.save_refresh_token(refresh_token=user_refresh_token)
