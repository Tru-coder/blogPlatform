from typing import Annotated, List
from uuid import UUID

from fastapi import APIRouter, Response, status, Path, Depends

from src.auth.permission import Permission
from src.auth.permitssion_checker import PermissionChecker
from src.configs.depends import TagServiceDep, PaginatorDep, TimeIntervalDep
from src.domain.app_user import AppUser
from src.http_schemas.tag_schema import GetTagsSchema, CreateTagSchema

tag_router = APIRouter(
    prefix="/tags",
    tags=["tags"],
)


@tag_router.get("/", response_model=List[GetTagsSchema])
async def get_tags(
        response: Response,
        tag_service: TagServiceDep,
        paginator: PaginatorDep,
        time_interval: TimeIntervalDep
):
    total_count = await tag_service.count_query_result_with_interval(
        filters={},
        time_interval=time_interval
    )
    response.headers["X-Total-Count"] = str(total_count)

    data = await tag_service.get_entities_with_filters_and_interval(
        filters={},
        period=time_interval,
        paginator=paginator
    )

    return data


@tag_router.get("/{tag_uuid}", response_model=GetTagsSchema)
async def get_tag_by_uuid(
        tag_uuid: Annotated[UUID, Path(description="UUID тега")],
        tag_service: TagServiceDep,
):
    return await tag_service.get_entity_by_uuid(entity_uuid=tag_uuid)


@tag_router.post("/", status_code=status.HTTP_201_CREATED, response_model=GetTagsSchema)
async def create_tag(
        tag_service: TagServiceDep,
        request_body: CreateTagSchema,
        _: AppUser = Depends(
            PermissionChecker(required_permissions=[Permission.TAG_CREATE])
        )
):
    return await tag_service.create_tag(request_body=request_body)


@tag_router.patch("/{tag_uuid}", response_model=GetTagsSchema)
async def update_tag(
        tag_uuid: Annotated[UUID, Path(description="UUID тега")],
        tag_service: TagServiceDep,
        request_body: CreateTagSchema,
        _: AppUser = Depends(
            PermissionChecker(required_permissions=[Permission.TAG_UPDATE])
        )
):
    return await tag_service.update_tag(tag_uuid=tag_uuid, request_body=request_body)


@tag_router.delete("/{tag_uuid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_all_tags(
        tag_service: TagServiceDep,
        tag_uuid: Annotated[UUID, Path(description="UUID тега")],
        _: AppUser = Depends(
            PermissionChecker(required_permissions=[Permission.TAG_DELETE])
        )
):
    await tag_service.delete_entity_by_uuid(entity_uuid=tag_uuid)
