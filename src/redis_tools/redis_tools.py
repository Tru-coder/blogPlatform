import json
from functools import wraps
from typing import Any, Callable, TypeVar, ParamSpec, List, Awaitable, cast

import redis.asyncio as redis
from arq.connections import RedisSettings

from src.configs.settings import app_settings
from src.domain.post import Post
from src.logger.app_logger import AppLogger
from src.utils.custom_json_encoder import CustomJSONEncoder

P = ParamSpec("P")
R = TypeVar("R", bound=List[Post])

class RedisTools:
    __redis_client = redis.Redis(
        host=app_settings.REDIS_HOST,
        port=app_settings.REDIS_PORT,
        decode_responses=True
    )

    AppLogger.custom_logger.critical(
        f"Redis инициализирован хост={app_settings.REDIS_HOST} и порт={app_settings.REDIS_PORT}")

    @classmethod
    def cache_find_published_posts(cls, ex: int = 60, session_kwarg_name: str = "session") -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]:
        def decorator(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
            @wraps(func)
            async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                key_parts = [
                    getattr(func, "__module__", ""),
                    getattr(func, "__qualname__", "")
                ]
                # Исключаем self из ключа кэша (если есть)
                if args:
                    relevant_args = args[1:]  # пропускаем self
                else:
                    relevant_args = args
                key_parts += map(str, relevant_args)

                # Исключаем session из kwargs
                filtered_kwargs = {k: v for k, v in kwargs.items() if k != session_kwarg_name}
                key_parts += (f"{k}={v}" for k, v in sorted(filtered_kwargs.items()))
                cache_key = ":".join(filter(None, key_parts))

                cached = await cls.get_key(cache_key)
                if cached is not None:
                    AppLogger.custom_logger.info(f"Redis cache hit: {cache_key}")
                    data = json.loads(cached)
                    return cast(R, [Post(**item) for item in data])

                result: List[Post] = await func(*args, **kwargs)
                json_result = json.dumps([obj.to_dict() for obj in result], cls=CustomJSONEncoder)
                await cls.set_key(cache_key, json_result, ex_in_sec=ex)
                AppLogger.custom_logger.info(f"Redis cache set: {cache_key}, value={json_result}")
                return cast(R, result)

            return wrapper

        return decorator

    @classmethod
    async def set_key(
            cls, key: Any, value: Any, ex_in_sec: int | None = None, keep_ttl: bool = False
    ) -> None:
        await cls.__redis_client.set(
            key, value, ex=ex_in_sec, keepttl=keep_ttl
        )

    @classmethod
    async def get_key(cls, key: Any) -> Any:
        return await cls.__redis_client.get(key)

    @classmethod
    async def get_keys(cls):
        return await cls.__redis_client.keys(pattern='*')

    @classmethod
    async def disconnect(cls):
        await cls.__redis_client.aclose()

    @classmethod
    async def get_ttl(cls, name: str):
        return await cls.__redis_client.ttl(name)

    @classmethod
    async def del_key(cls, key: Any) -> None:
        await cls.__redis_client.delete(key)

    @classmethod
    def scheduler_settings(cls) -> RedisSettings:
        return RedisSettings(
            app_settings.REDIS_HOST,
            app_settings.REDIS_PORT
        )
