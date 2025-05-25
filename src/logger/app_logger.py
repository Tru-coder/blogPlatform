import enum
import logging
import sys
import time
from functools import wraps
from inspect import iscoroutinefunction
from typing import Awaitable, Callable, Protocol, overload

from typing_extensions import TypeIs

from src.logger.custom_formatter import CustomFormatter


def is_coroutine[**P, R](
        func: Callable[P, R | Awaitable[R]],
) -> TypeIs[Callable[P, Awaitable[R]]]:
    return iscoroutinefunction(func)


class SyncOrAsync(Protocol):
    @overload
    def __call__[**P, R](
            self, _func: Callable[P, Awaitable[R]]
    ) -> Callable[P, Awaitable[R]]:
        ...

    @overload
    def __call__[**P, R](self, _func: Callable[P, R]) -> Callable[P, R]:
        ...

    def __call__[**P, R](
            self, _func: Callable[P, Awaitable[R]] | Callable[P, R]
    ) -> Callable[P, Awaitable[R]] | Callable[P, R]:
        ...


@enum.unique
class LogLevel(enum.Enum):
    DEBUG = 'DEBUG'
    INFO = 'INFO'
    WARNING = 'WARNING'
    ERROR = 'ERROR'
    EXCEPTION = 'EXCEPTION'
    CRITICAL = 'CRITICAL'


class AppLogger:
    custom_logger = logging.getLogger(__name__)
    stream_handler = logging.StreamHandler(sys.stdout)

    stream_handler.setFormatter(CustomFormatter())
    custom_logger.handlers = [stream_handler]

    custom_logger.setLevel(logging.DEBUG)

    log_level_call: dict[LogLevel, Callable] = {
        LogLevel.DEBUG: custom_logger.debug,
        LogLevel.INFO: custom_logger.info,
        LogLevel.WARNING: custom_logger.warning,
        LogLevel.EXCEPTION: custom_logger.exception,
        LogLevel.ERROR: custom_logger.error,
        LogLevel.CRITICAL: custom_logger.critical
    }
    custom_logger.critical("Logger class initialized")

    @classmethod
    def log(cls, log_level: LogLevel = LogLevel.DEBUG) -> SyncOrAsync:
        @overload
        def decorator[**P, R](
                _func: Callable[P, Awaitable[R]],
        ) -> Callable[P, Awaitable[R]]:
            ...

        @overload
        def decorator[**P, R](
                _func: Callable[P, R],
        ) -> Callable[P, R]:
            ...

        def decorator[**P, R](
                _func: Callable[P, Awaitable[R]] | Callable[P, R],
        ) -> Callable[P, Awaitable[R]] | Callable[P, R]:
            if is_coroutine(_func):
                _awaitable_func = _func

                @wraps(_awaitable_func)
                async def _async_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                    cls.log_level_call[log_level](f"Calling {_awaitable_func.__name__}({args}, {kwargs}) "
                                                  f"with {args}, {kwargs}")
                    res = await _awaitable_func(*args, **kwargs)

                    cls.log_level_call[log_level](f"Function: {_awaitable_func.__name__}({args}, {kwargs}) "
                                                  f"returned {res}")

                    return res

                return _async_wrapper


            else:
                @wraps(_func)
                def _sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                    cls.log_level_call[log_level](f"Calling {_func.__name__}({args}, {kwargs}) "
                                                  f"with {args}, {kwargs}")
                    res = _func(*args, **kwargs)

                    cls.log_level_call[log_level](f"Function: {_func.__name__}({args}, {kwargs}) "
                                                  f"returned {res}")
                    return res

                return _sync_wrapper

        return decorator

    @classmethod
    def measure_execution(cls, log_level: LogLevel = LogLevel.DEBUG) -> SyncOrAsync:
        @overload
        def decorator[**P, R](
                _func: Callable[P, Awaitable[R]],
        ) -> Callable[P, Awaitable[R]]:
            ...

        @overload
        def decorator[**P, R](
                _func: Callable[P, R],
        ) -> Callable[P, R]:
            ...

        def decorator[**P, R](
                _func: Callable[P, Awaitable[R]] | Callable[P, R],
        ) -> Callable[P, Awaitable[R]] | Callable[P, R]:
            if is_coroutine(_func):
                _awaitable_func = _func

                @wraps(_awaitable_func)
                async def _async_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                    start_time = time.time()
                    res = await _awaitable_func(*args, **kwargs)
                    cls.log_level_call[log_level](
                        f"Время выполнения '{_awaitable_func.__name__}' is '{time.time() - start_time}'"
                    )
                    return res

                return _async_wrapper

            else:
                @wraps(_func)
                def _sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                    start_time = time.time()
                    res = _func(*args, **kwargs)
                    cls.log_level_call[log_level](
                        f"Время выполнения '{_func.__name__}' is '{time.time() - start_time}'"
                    )
                    return res

                return _sync_wrapper

        return decorator
