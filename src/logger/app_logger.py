import enum
import inspect
import logging
import sys
import time
from functools import wraps
from typing import Callable, ParamSpec, TypeVar

from src.logger.custom_formatter import CustomFormatter


@enum.unique
class LogLevel(enum.Enum):
    DEBUG = 'DEBUG'
    INFO = 'INFO'
    WARNING = 'WARNING'
    ERROR = 'ERROR'
    EXCEPTION = 'EXCEPTION'
    CRITICAL = 'CRITICAL'


F_Spec = ParamSpec("F_Spec")
F_Return = TypeVar("F_Return")


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
    def log(cls, log_level: LogLevel = LogLevel.DEBUG):
        """Log decorator"""

        def real_log(func: Callable[F_Spec, F_Return]) -> Callable[F_Spec, F_Return]:
            """Log function"""

            @wraps(func)
            async def async_trace(*args: F_Spec, **kwargs: F_Spec) -> F_Return:
                """Async wrapper"""
                cls.log_level_call[log_level](f"Calling {func.__name__}({args}, {kwargs}) "
                                              f"with {args}, {kwargs}")

                original_result = await func(*args, **kwargs)

                cls.log_level_call[log_level](f"Function: {func.__name__}({args}, {kwargs}) "
                                              f"returned {original_result}")

                return original_result

            @wraps(func)
            def sync_trace(*args: F_Spec, **kwargs: F_Spec) -> F_Return:
                """Sync wrapper"""
                cls.log_level_call[log_level](f"Calling {func.__name__}({args}, {kwargs}) "
                                              f"with {args}, {kwargs}")

                original_result = func(*args, **kwargs)

                cls.log_level_call[log_level](f"Function: {func.__name__}({args}, {kwargs}) "
                                              f"returned {original_result}")

                return original_result

            return async_trace if inspect.iscoroutinefunction(func) else sync_trace

        return real_log

    @classmethod
    def measure_execution(cls, log_level: LogLevel):
        def real_measure(func: Callable[F_Spec, F_Return]) -> Callable[F_Spec, F_Return]:
            @wraps(func)
            async def async_measure(*args: F_Spec, **kwargs: F_Spec) -> F_Return:
                start_time = time.time()
                original_result = await func(*args, **kwargs)

                cls.log_level_call[log_level](
                    f"Время выполнения '{func.__name__}' is '{time.time() - start_time}'")

                return original_result

            @wraps(func)
            def sync_measure(*args: F_Spec, **kwargs: F_Spec) -> F_Return:
                start_time = time.time()
                original_result = func(*args, **kwargs)

                cls.log_level_call[log_level](
                    f"Время выполнения'{func.__name__}' is '{time.time() - start_time}'")

                return original_result

            return async_measure if inspect.iscoroutinefunction(func) else sync_measure

        return real_measure
