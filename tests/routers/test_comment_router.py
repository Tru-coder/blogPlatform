from typing import AsyncGenerator
from uuid import UUID

import pytest
from fastapi import status
from httpx import AsyncClient

from src.domain.enums.enums import PostStatus
from src.http_schemas.comment_schema import CreateCommentSchema
from src.http_schemas.post_schemas import CreatePostSchema
from src.services.comment_service import CommentService


@pytest.mark.anyio
async def test_get_to_moderate_comments_admin(admin_client: AsyncClient):
    response = await admin_client.get("/comments/to-moderate")
    assert response.status_code == status.HTTP_200_OK
    assert "X-Total-Count" in response.headers
    assert isinstance(response.json(), list)


@pytest.mark.anyio
async def test_get_to_moderate_comments_author(author_client: AsyncClient):
    response = await author_client.get("/comments/to-moderate")
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.anyio
async def test_get_to_moderate_comments_anonym(anonym_client: AsyncClient):
    response = await anonym_client.get("/comments/to-moderate")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.fixture
async def published_post(author_client, mock_post_service) -> AsyncGenerator[dict[str, str], None]:
    post_data = CreatePostSchema(
        title="Published Post",
        content="Published content",
        category="Песочница",
        status=PostStatus.PUBLISHED,
        tags=[],
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


@pytest.fixture
async def draft_post(author_client, mock_post_service):
    post_data = CreatePostSchema(
        title="Draft Post",
        content="Draft content",
        category="Песочница",
        status=PostStatus.DRAFT,
        tags=[],
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
async def test_create_comment_on_published_post(author_client: AsyncClient, published_post: dict[str, str], mock_comment_service: CommentService):
    comment_data = CreateCommentSchema(
        post_uuid=UUID(published_post["uuid"]),
        parent_comment_uuid=None,
        content="Comment on published post"
    )
    response = await author_client.post(
        "/comments/",
        content=comment_data.model_dump_json()
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["content"] == "Comment on published post"
    await mock_comment_service.delete_entity_by_uuid(entity_uuid=data["uuid"])


@pytest.mark.anyio
async def test_create_comment_on_draft_post_forbidden(author_client: AsyncClient, draft_post: dict[str, str]):
    comment_data = CreateCommentSchema(
        post_uuid=UUID(draft_post["uuid"]),
        parent_comment_uuid=None,
        content="Should not be allowed"
    )
    response = await author_client.post(
        "/comments/",
        content=comment_data.model_dump_json()
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.anyio
async def test_create_nested_comment_on_published_post(author_client: AsyncClient, published_post: dict[str, str], mock_comment_service: CommentService):
    # Сначала создаём родительский комментарий
    parent_comment_data = CreateCommentSchema(
        post_uuid=UUID(published_post["uuid"]),
        parent_comment_uuid=None,
        content="Parent comment"
    )
    parent_response = await author_client.post(
        "/comments/",
        content=parent_comment_data.model_dump_json()
    )
    assert parent_response.status_code == status.HTTP_201_CREATED
    parent_comment = parent_response.json()

    # Теперь создаём вложенный комментарий
    nested_comment_data = CreateCommentSchema(
        post_uuid=UUID(published_post["uuid"]),
        parent_comment_uuid=parent_comment["uuid"],
        content="Nested comment"
    )
    nested_response = await author_client.post(
        "/comments/",
        content=nested_comment_data.model_dump_json()
    )
    assert nested_response.status_code == status.HTTP_201_CREATED
    nested_comment = nested_response.json()
    assert nested_comment["content"] == "Nested comment"

    # Clean up
    await mock_comment_service.delete_entity_by_uuid(entity_uuid=parent_comment["uuid"])
    await mock_comment_service.delete_entity_by_uuid(entity_uuid=nested_comment["uuid"])

