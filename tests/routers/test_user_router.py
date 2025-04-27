import pytest

from src.domain.app_user import AppUser
from src.http_schemas.user_schemas import UserRegisterSchema
from src.services.user_service import UserService


from fastapi import status
from httpx import AsyncClient

@pytest.fixture(scope="function")
async def deletable_user(mock_user_service: UserService):
    user = await mock_user_service.user_register(
        request_body=UserRegisterSchema(
            login="todelete@yandex.ru",
            password="password",
            role_value="AUTHOR"
        )
    )
    yield user
    await mock_user_service.delete_entity_by_uuid(entity_uuid=user.uuid)

@pytest.mark.anyio
async def test_get_users_admin(admin_client: AsyncClient):
    response = await admin_client.get("/users/")
    assert response.status_code == status.HTTP_200_OK
    # Проверяем наличие заголовка X-Total-Count
    assert "X-Total-Count" in response.headers
    # Проверяем, что ответ — список пользователей
    assert isinstance(response.json(), list)

@pytest.mark.anyio
async def test_get_users_anonymous(anonym_client: AsyncClient):
    response = await anonym_client.get("/users/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.anyio
async def test_get_users_author(author_client: AsyncClient):
    response = await author_client.get("/users/")
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.anyio
async def test_delete_user_admin(admin_client: AsyncClient, deletable_user: AppUser):
    response = await admin_client.delete(f"/users/{deletable_user.uuid}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

@pytest.mark.anyio
async def test_delete_user_author(author_client: AsyncClient, deletable_user: AppUser):
    response = await author_client.delete(f"/users/{deletable_user.uuid}")
    assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.anyio
async def test_delete_user_anonym(anonym_client: AsyncClient, deletable_user: AppUser):
    response = await anonym_client.delete(f"/users/{deletable_user.uuid}")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED



@pytest.mark.anyio
async def test_user_register_success(anonym_client: AsyncClient, mock_user_service: UserService):
    # Данные нового пользователя
    user_data = UserRegisterSchema(
        login="newuser@yandex.ru",
        password="testpassword",
        role_value="AUTHOR"
    )
    response = await anonym_client.post(
        "/users/",
        content=user_data.model_dump_json(exclude={"role"})
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["login"] == "newuser@yandex.ru"
    assert data["role_repr"] == "AUTHOR"
    # Чистим БД после теста
    await mock_user_service.delete_entity_by_uuid(entity_uuid=data["uuid"])

@pytest.mark.anyio
async def test_user_register_duplicate(anonym_client: AsyncClient, mock_user_service: UserService):
    # Регистрируем пользователя
    user_data = UserRegisterSchema(
        login="dupuser@yandex.ru",
        password="testpassword",
        role_value="USER"
    )
    response1 = await anonym_client.post(
        "/users/",
        content=user_data.model_dump_json(exclude={"role"})
    )
    assert response1.status_code == status.HTTP_201_CREATED
    # Повторная регистрация с тем же логином
    response2 = await anonym_client.post(
        "/users/",
        content=user_data.model_dump_json(exclude={"role"})
    )
    assert response2.status_code == status.HTTP_400_BAD_REQUEST
    # Чистим БД
    data = response1.json()
    await mock_user_service.delete_entity_by_uuid(entity_uuid=data["uuid"])