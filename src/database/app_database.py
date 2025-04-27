from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import DeclarativeBase

from src.configs.settings import app_settings
from src.logger.app_logger import AppLogger


class Base(DeclarativeBase):
    # https://alembic.sqlalchemy.org/en/latest/naming.html
    metadata = MetaData(naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_`%(constraint_name)s`",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s"
    })


class AppDatabase:
    engine = create_async_engine(app_settings.DB_URL, echo=True)
    AppLogger.custom_logger.critical(msg=f"Database URL={engine.url}")

    @classmethod
    async def create_tables(cls) -> None:
        async with cls.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    @classmethod
    async def drop_tables(cls) -> None:
        async with cls.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
