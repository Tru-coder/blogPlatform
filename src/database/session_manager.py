import time
from functools import wraps
from typing import ParamSpec, TypeVar, Any, Coroutine, Callable

from sqlalchemy.ext.asyncio import async_sessionmaker

from src.database.app_database import AppDatabase
from src.logger.app_logger import AppLogger


P = ParamSpec("P")
R = TypeVar("R")

class SessionManager:
    async_session_maker = async_sessionmaker(
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
        bind=AppDatabase.engine
    )

    @classmethod
    def generate_async_transaction(cls, session_kwarg_name: str = "session"):
        def transactional(func: Callable[P, Coroutine[Any, Any, R]]) -> Callable[P, Coroutine[Any, Any, R]]:
            @wraps(func)
            async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                if kwargs.get(session_kwarg_name) is not None:
                    return await func(*args, **kwargs)

                async with cls.async_session_maker.begin() as session:
                    AppLogger.custom_logger.debug(
                        f"Database session for {func.__name__} was generated")
                    start_time = time.time()

                    kwargs[session_kwarg_name] = session

                    original_result = await func(*args, **kwargs)

                    AppLogger.custom_logger.debug(
                        f"Database session for {func.__name__} was opened for {time.time() - start_time}s")
                return original_result

            return wrapper

        return transactional
