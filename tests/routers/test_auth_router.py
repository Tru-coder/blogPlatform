import pytest
from fastapi import status
from httpx import AsyncClient

from src.services.user_service import UserService

from src.domain.app_user import AppUser
from src.http_schemas.auth_schema import UserLogin
from src.http_schemas.user_schemas import UserRegisterSchema


@pytest.fixture(scope="function")
async def prepare_user_data(mock_user_service: UserService):
    user = await mock_user_service.user_register(
        request_body=UserRegisterSchema(
            login="testuser1@yandex.ru",
            password="correct_password",
            role_value="ADMIN"
        )
    )
    yield user

    await mock_user_service.delete_entity_by_uuid(entity_uuid=user.uuid)


@pytest.mark.anyio
async def test_login_success(anonym_client: AsyncClient, prepare_user_data: AppUser):
    response = await anonym_client.post(
        "/auth/login",
        content=UserLogin(
            login="testuser1@yandex.ru",
            password="correct_password"
        ).model_dump_json(),
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"message": "OK"}
    # Проверяем наличие куки
    cookies = response.cookies
    assert "access_token" in cookies
    assert "refresh_token" in cookies


@pytest.mark.anyio
async def test_login_invalid_credentials(anonym_client: AsyncClient, prepare_user_data: AppUser):
    response = await anonym_client.post(
        "/auth/login",
        content=UserLogin(
            login=prepare_user_data.login,
            password="incorrect_password"
        ).model_dump_json(),
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    # Проверяем, что куки не установлены
    cookies = response.cookies
    assert "access_token" not in cookies
    assert "refresh_token" not in cookies


@pytest.mark.anyio
async def test_logout_unauthorized(anonym_client: AsyncClient):
    logout_response = await anonym_client.post("/auth/logout")
    assert logout_response.status_code == status.HTTP_401_UNAUTHORIZED
    assert logout_response.json()["detail"] == "Unauthorized"



@pytest.mark.anyio
async def test_refresh_token_success(anonym_client: AsyncClient, prepare_user_data: AppUser):
    response = await anonym_client.post(
        "/auth/login",
        content=UserLogin(
            login=prepare_user_data.login,
            password="correct_password"
        ).model_dump_json(),
    )
    response = await anonym_client.post("/auth/refresh-token")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"message": "OK"}
    # Проверяем, что access_token обновился
    set_cookie_headers = response.headers.get_list("set-cookie")
    assert any("access_token=" in h for h in set_cookie_headers)

@pytest.mark.anyio
async def test_refresh_token_unauthorized(anonym_client: AsyncClient):
    # anonym_client не содержит refresh_token
    response = await anonym_client.post("/auth/refresh-token")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Unauthorized"