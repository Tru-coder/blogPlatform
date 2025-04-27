import pytest
from fastapi import status
from httpx import AsyncClient

from src.services.tag_service import TagService


@pytest.fixture(scope="function")
async def created_tag(admin_client: AsyncClient, mock_tag_service):
    tag_data = {"name": "test-tag"}
    response = await admin_client.post("/tags/", json=tag_data)
    assert response.status_code == status.HTTP_201_CREATED
    tag = response.json()
    yield tag
    await mock_tag_service.delete_entity_by_uuid(entity_uuid=tag["uuid"])

@pytest.mark.anyio
async def test_create_tag_admin(admin_client: AsyncClient, mock_tag_service):
    tag_data = {"name": "unique-tag"}
    response = await admin_client.post("/tags/", json=tag_data)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == "unique-tag"
    await mock_tag_service.delete_entity_by_uuid(entity_uuid=data["uuid"])

@pytest.mark.anyio
async def test_create_tag_duplicate_name(admin_client: AsyncClient, created_tag):
    # Попытка создать тег с тем же именем
    tag_data = {"name": created_tag["name"]}
    response = await admin_client.post("/tags/", json=tag_data)
    assert response.status_code in (status.HTTP_400_BAD_REQUEST, status.HTTP_409_CONFLICT)

@pytest.mark.anyio
async def test_create_tag_forbidden(author_client):
    tag_data = {"name": "author-tag"}
    response = await author_client.post("/tags/", json=tag_data)
    assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.anyio
async def test_create_tag_unauthorized(anonym_client):
    tag_data = {"name": "anon-tag"}
    response = await anonym_client.post("/tags/", json=tag_data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.anyio
async def test_patch_tag_admin(admin_client: AsyncClient, created_tag, mock_tag_service):
    patch_data = {"name": "patched-tag"}
    response = await admin_client.patch(f"/tags/{created_tag['uuid']}", json=patch_data)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == "patched-tag"
    # Clean up
    await mock_tag_service.delete_entity_by_uuid(entity_uuid=created_tag["uuid"])

@pytest.mark.anyio
async def test_patch_tag_forbidden(author_client: AsyncClient, created_tag):
    patch_data = {"name": "fail-patch"}
    response = await author_client.patch(f"/tags/{created_tag['uuid']}", json=patch_data)
    assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.anyio
async def test_patch_tag_unauthorized(anonym_client: AsyncClient, created_tag):
    patch_data = {"name": "fail-patch"}
    response = await anonym_client.patch(f"/tags/{created_tag['uuid']}", json=patch_data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.anyio
async def test_delete_tag_admin(admin_client: AsyncClient, mock_tag_service: TagService):
    tag_data = {"name": "to-delete"}
    response = await admin_client.post("/tags/", json=tag_data)
    assert response.status_code == status.HTTP_201_CREATED
    tag_uuid = response.json()["uuid"]
    del_response = await admin_client.delete(f"/tags/{tag_uuid}")
    assert del_response.status_code == status.HTTP_204_NO_CONTENT
    await mock_tag_service.delete_entity_by_uuid(entity_uuid=tag_uuid)

@pytest.mark.anyio
async def test_delete_tag_forbidden(author_client, created_tag):
    response = await author_client.delete(f"/tags/{created_tag['uuid']}")
    assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.anyio
async def test_delete_tag_unauthorized(anonym_client, created_tag):
    response = await anonym_client.delete(f"/tags/{created_tag['uuid']}")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED