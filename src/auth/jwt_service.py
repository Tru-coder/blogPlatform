import enum
import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Any, Self

import jwt
from fastapi import HTTPException, status

from src.configs.settings import app_settings
from src.logger.app_logger import AppLogger
from src.redis_tools.redis_tools import RedisTools
from src.utils.custom_json_encoder import CustomJSONEncoder


# Model to store refresh tokens in Redis
@dataclass
class RefreshToken:
    jti: uuid.UUID
    created_at: datetime
    expired_at: datetime
    subject: str
    revoked: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            'jti': str(self.jti),
            'created_at': self.created_at.isoformat(),
            'expired_at': self.expired_at.isoformat(),
            'subject': self.subject,
            'revoked': self.revoked
        }

    @classmethod
    def refresh_token_hook(cls, data: dict[str, Any]) -> Self:
        # for json loads hook
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['expired_at'] = datetime.fromisoformat(data['expired_at'])
        return cls(**data)


@enum.unique
class TokenType(enum.Enum):
    ACCESS = "access"
    REFRESH = "refresh"


class JWTService:

    with open(app_settings.JWT_PRIVATE_KEY_FILE_PATH, 'rb') as f:
        private_key = f.read()

    with open(app_settings.JWT_PUBLIC_KEY_FILE_PATH, 'rb') as f:
        public_key = f.read()

    algorithm = app_settings.JWT_ALGORITHM
    access_expiration = app_settings.JWT_ACCESS_EXPIRATION_IN_SECONDS
    refresh_expiration = app_settings.JWT_REFRESH_EXPIRATION_IN_SECONDS
    issuer = app_settings.JWT_ISSUER
    audience = app_settings.JWT_AUDIENCE
    redis_token_prefix = app_settings.JWT_REDIS_PREFIX

    @classmethod
    def generate_jti(cls):
        return uuid.uuid4()


    @classmethod
    @AppLogger.measure_execution()
    def encode_jwt(cls, payload: dict[str, Any]) -> str:
        payload["nbf"] = datetime.now(tz=timezone.utc)
        payload["iss"] = cls.issuer
        payload["aud"] = cls.audience
        payload["iat"] = datetime.now(tz=timezone.utc)

        return jwt.encode(
            payload=payload,
            key=cls.private_key,
            algorithm=cls.algorithm,
            json_encoder=CustomJSONEncoder,
        )

    @classmethod
    def decode_jwt(cls, jwt_token: str) -> dict[str, Any]:
        return jwt.decode(
            jwt=jwt_token,
            audience=cls.audience,
            issuer=cls.issuer,
            leeway=app_settings.JWT_LEEWAY_IN_SECONDS,
            key=cls.public_key,
            algorithms=[cls.algorithm],
            options={"require": ["exp", "nbf", "iat", "iss", "aud"]}
        )

    @classmethod
    def generate_access_token(cls, payload: dict[str, Any]) -> str:
        payload["token_type"] = TokenType.ACCESS
        payload["exp"] = datetime.now(tz=timezone.utc) + timedelta(seconds=cls.access_expiration)
        return cls.encode_jwt(payload=payload)

    @classmethod
    def generate_refresh_token(cls, payload: dict[str, Any]) -> str:
        payload["token_type"] = TokenType.REFRESH
        payload["exp"] = datetime.now(tz=timezone.utc) + timedelta(seconds=cls.refresh_expiration)
        payload["jti"] = cls.generate_jti()
        AppLogger.custom_logger.info(f"Refresh токен создан. Token={payload['jti']}")
        return cls.encode_jwt(payload=payload)

    @classmethod
    async def save_refresh_token(cls, refresh_token: RefreshToken) -> None:
        # blacklist implementation
        # for revoking refresh token
        await RedisTools.set_key(
            key=cls.redis_token_prefix + str(refresh_token.jti),
            value=json.dumps(refresh_token.to_dict(), cls=CustomJSONEncoder),
            ex_in_sec=int((refresh_token.expired_at - datetime.now(tz=timezone.utc)).total_seconds()),
        )

    @classmethod
    async def get_user_token_by_jti(cls, jti:  uuid.UUID) -> RefreshToken:
        token_data = await RedisTools.get_key(key=cls.redis_token_prefix + str(jti))
        if token_data is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

        return json.loads(token_data, object_hook=RefreshToken.refresh_token_hook)

    @classmethod
    async def revoke_refresh_token(cls, jti: uuid.UUID) -> None:
        refresh_token = await cls.get_user_token_by_jti(jti=jti)
        refresh_token.revoked = True
        await cls.save_refresh_token(refresh_token=refresh_token)
