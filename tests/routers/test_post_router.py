from typing import AsyncGenerator

import pytest
from fastapi import status
from httpx import AsyncClient

from src.domain.post import PostStatus
from src.http_schemas.post_schemas import CreatePostSchema, UpdatePostSchema
from src.http_schemas.tag_schema import CreateTagSchema
from src.services.post_service import PostService
from src.services.tag_service import TagService


@pytest.fixture(scope="function")
async def existing_tag(admin_client: AsyncClient, mock_tag_service: TagService) -> dict[str, str]:
    tag_data = CreateTagSchema(name="test-tag")
    response = await admin_client.post(
        "/tags/",
        content=tag_data.model_dump_json()
    )
    assert response.status_code == status.HTTP_201_CREATED
    tag = response.json()
    yield tag
    await mock_tag_service.delete_entity_by_uuid(entity_uuid=tag["uuid"])


@pytest.mark.anyio
async def test_create_post_admin(admin_client: AsyncClient, existing_tag: dict[str, str],
                                 mock_post_service: PostService):
    post_data = CreatePostSchema(
        title="Admin Post",
        content="Admin content",
        category="Песочница",
        status=PostStatus.DRAFT,
        tags=[existing_tag["name"]],
        to_published_at=None
    )
    response = await admin_client.post(
        "/posts/",
        content=post_data.model_dump_json()
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["title"] == "Admin Post"
    assert data['uuid']
    await mock_post_service.delete_entity_by_uuid(entity_uuid=data["uuid"])


@pytest.mark.anyio
async def test_create_post_author(author_client: AsyncClient, existing_tag: dict[str, str],
                                  mock_post_service: PostService):
    post_data = CreatePostSchema(
        title="Author Post",
        content="Author content",
        category="Песочница",
        status=PostStatus.DRAFT,
        tags=[existing_tag["name"]],
        to_published_at=None
    )
    response = await author_client.post(
        "/posts/",
        content=post_data.model_dump_json()
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["title"] == "Author Post"
    assert data['uuid']
    await mock_post_service.delete_entity_by_uuid(entity_uuid=data["uuid"])


@pytest.mark.anyio
async def test_create_post_unauthorized(anonym_client: AsyncClient, existing_tag: dict[str, str]):
    post_data = CreatePostSchema(
        title="Anon Post",
        content="Anon content",
        category="Песочница",
        status=PostStatus.DRAFT,
        tags=[existing_tag["name"]],
        to_published_at=None
    )
    response = await anonym_client.post(
        "/posts/",
        content=post_data.model_dump_json()
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.fixture
async def author_post(author_client: AsyncClient, existing_tag: dict[str, str], mock_post_service: PostService) \
        -> AsyncGenerator[dict[str, str], None]:
    post_data = CreatePostSchema(
        title="Original Title",
        content="Original Content",
        category="Песочница",
        status=PostStatus.PUBLISHED,
        tags=[existing_tag["name"]],
        to_published_at=None
    )
    response = await author_client.post(
        "/posts/",
        content=post_data.model_dump_json()
    )
    assert response.status_code == status.HTTP_201_CREATED
    post = response.json()
    yield post
    await mock_post_service.delete_entity_by_uuid(entity_uuid=post["uuid"])


@pytest.mark.anyio
async def test_update_own_post_author(
        author_client: AsyncClient, author_post: dict[str, str],
        existing_tag: dict[str, str], mock_post_service: PostService):

    update_data = UpdatePostSchema(
        title="Updated Title",
        to_published_at=None
    )
    response = await author_client.patch(
        f"/posts/{author_post['uuid']}",
        content=update_data.model_dump_json(exclude_unset=True)
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["title"] == "Updated Title"

@pytest.mark.anyio
async def test_update_not_your_post_admin(admin_client: AsyncClient, author_post: dict[str, str]):
    # Админ не автор этого поста, должен получить 404
    update_data = UpdatePostSchema(
        content="Цензура",
    )
    response = await admin_client.patch(
        f"/posts/{author_post['uuid']}",
        content=update_data.model_dump_json(exclude_unset=True)
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.anyio
async def test_update_not_your_post_author(
        author_client: AsyncClient, admin_client: AsyncClient, existing_tag: dict[str, str], mock_post_service: PostService
):
    # Сначала админ создаёт пост
    post_data = CreatePostSchema(
        title="Admin's Post",
        content="Admin Content",
        category="Песочница",
        status=PostStatus.PUBLISHED,
        tags=[existing_tag["name"]],
        to_published_at=None
    )
    response = await admin_client.post(
        "/posts/",
        content=post_data.model_dump_json()
    )
    assert response.status_code == status.HTTP_201_CREATED
    admin_post = response.json()
    # Теперь author пытается обновить чужой пост
    update_data = UpdatePostSchema(
        title="Авторское право",
    )
    response = await author_client.patch(
        f"/posts/{admin_post['uuid']}",
        content=update_data.model_dump_json(exclude_unset=True)
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    # Clean up
    await mock_post_service.delete_entity_by_uuid(entity_uuid=admin_post["uuid"])


@pytest.fixture(scope="function")
async def author_post_2(author_client, existing_tag, mock_post_service):
    post_data = CreatePostSchema(
        title="DeleteMe",
        content="To be deleted",
        category="Песочница",
        status="DRAFT",
        tags=[existing_tag["name"]],
        to_published_at=None
    )
    response = await author_client.post(
        "/posts/",
        content=post_data.model_dump_json()
    )
    assert response.status_code == status.HTTP_201_CREATED
    post = response.json()
    yield post
    # Не чистим, так как тесты удаляют

@pytest.mark.anyio
async def test_delete_own_post_author(author_client: AsyncClient, author_post: dict[str, str]):
    response = await author_client.delete(f"/posts/{author_post['uuid']}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

@pytest.mark.anyio
async def test_delete_post_admin(admin_client: AsyncClient, author_post:dict[str, str]):
    # Админ удаляет чужой пост
    response = await admin_client.delete(f"/posts/{author_post['uuid']}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

@pytest.mark.anyio
async def test_delete_not_your_post_author(
        author_client: AsyncClient, admin_client: AsyncClient, existing_tag: dict[str, str], mock_post_service: PostService
):
    # Сначала админ создаёт пост
    post_data = CreatePostSchema(
        title="Admin's Post",
        content="Admin Content",
        category="Песочница",
        status=PostStatus.DRAFT,
        tags=[existing_tag["name"]],
        to_published_at=None
    )
    response = await admin_client.post(
        "/posts/",
        content=post_data.model_dump_json()
    )
    assert response.status_code == status.HTTP_201_CREATED
    admin_post = response.json()
    # Теперь author пытается удалить чужой пост
    response = await author_client.delete(f"/posts/{admin_post['uuid']}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    assert await mock_post_service.get_entity_by_uuid(entity_uuid=admin_post["uuid"])
    # Clean up
    await mock_post_service.delete_entity_by_uuid(entity_uuid=admin_post["uuid"])