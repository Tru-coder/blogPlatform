import os
import time
from fastapi import status
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from src.configs.depends import user_service, tag_service, post_service, comment_service
from src.database.app_database import AppDatabase
from src.database.session_manager import SessionManager
from src.http_schemas.auth_schema import UserLogin
from src.http_schemas.user_schemas import UserRegisterSchema
from src.main import app
from src.services.comment_service import CommentService
from src.services.post_service import PostService
from src.services.tag_service import TagService
from src.services.user_service import UserService


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

@pytest.fixture(scope="session", autouse=True)
async def async_db_url(anyio_backend):
    db_url = os.environ.get("TEST_ASYNC_DB_URL")

    if not db_url:
        raise ValueError("TEST_ASYNC_DB_URL is not set")

    return db_url

@pytest.fixture(scope="session", autouse=True)
async def mock_database(anyio_backend, async_db_url):
    AppDatabase.engine = create_async_engine(async_db_url, echo=True, poolclass=NullPool)

    SessionManager.async_session_maker = async_sessionmaker(
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
        bind=AppDatabase.engine
    )


@pytest.fixture(scope="function", autouse=True)
async def footer_function_scope(anyio_backend):
    """Сообщает продолжительность теста после каждой функции."""
    start = time.time()
    yield
    stop = time.time()
    delta = stop - start
    print('\ntest duration : {:0.3} seconds'.format(delta))


@pytest.fixture(scope="function")
async def anonym_client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="https://test/api/v1/") as client:
        yield client


@pytest.fixture(scope="session", autouse=True)
async def setup_db():
    await AppDatabase.drop_tables()
    await AppDatabase.create_tables()
    yield
    await AppDatabase.drop_tables()

@pytest.fixture(scope="session")
async def mock_user_service() -> UserService:
    return user_service

@pytest.fixture(scope="session")
async def admin_client(mock_user_service: UserService):
    admin = await mock_user_service.user_register(
        request_body=UserRegisterSchema(
            login="admin@yandex.ru",
            password="correct_password",
            role_value="ADMIN"
        )
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test/api/v1/") as client:
        response = await client.post(
            '/auth/login',
            content=UserLogin(
                login=admin.login,
                password="correct_password"
            ).model_dump_json()
        )

        assert response.status_code == status.HTTP_200_OK
        client.cookies = response.cookies
        yield client

    await mock_user_service.delete_entity_by_uuid(entity_uuid=admin.uuid)


@pytest.fixture(scope="session")
async def author_client(mock_user_service: UserService):
    author = await mock_user_service.user_register(
        request_body=UserRegisterSchema(
            login="author@yandex.ru",
            password="correct_password",
            role_value="AUTHOR"
        )
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test/api/v1/") as client:
        response = await client.post(
            '/auth/login',
            content=UserLogin(
                login=author.login,
                password="correct_password"
            ).model_dump_json()
        )

        assert response.status_code == status.HTTP_200_OK
        client.cookies = response.cookies
        yield client

    await mock_user_service.delete_entity_by_uuid(entity_uuid=author.uuid)

@pytest.fixture(scope="session")
def mock_tag_service() -> TagService:
    return tag_service

@pytest.fixture(scope="session")
def mock_post_service() -> PostService:
    return post_service

@pytest.fixture(scope="session")
def mock_comment_service() -> CommentService:
    return comment_service