from typing import List, Annotated
from uuid import UUID

from fastapi import APIRouter, Response, Path, status, Depends

from src.auth.permission import Permission
from src.auth.permitssion_checker import PermissionChecker
from src.configs.depends import UserServiceDep, PaginatorDep, TimeIntervalDep
from src.domain.app_user import AppUser
from src.http_schemas.user_schemas import GetUsersSchema, UserRegisterSchema

user_router = APIRouter(
    prefix="/users",
    tags=["users"],
)


@user_router.get("/", response_model=List[GetUsersSchema])
async def get_users(
        response: Response,
        user_service: UserServiceDep,
        paginator: PaginatorDep,
        time_interval: TimeIntervalDep,
        _ : Annotated[AppUser, Depends(PermissionChecker(required_permissions=[Permission.USER_READ]))]
):
    total_count = await user_service.count_query_result_with_interval(
        filters={},
        time_interval=time_interval
    )
    response.headers["X-Total-Count"] = str(total_count)

    data = await user_service.get_entities_with_filters_and_interval(
        filters={},
        period=time_interval,
        paginator=paginator
    )

    return data


@user_router.get("/{user_uuid}", response_model=GetUsersSchema)
async def get_user(
        user_uuid: Annotated[UUID, Path(description="UUID пользователя")],
        user_service: UserServiceDep,
):
    return await user_service.get_entity_by_uuid(
        entity_uuid=user_uuid
    )


@user_router.post("/", status_code=status.HTTP_201_CREATED, response_model=GetUsersSchema)
async def user_register(
        user_service: UserServiceDep,
        request_body: UserRegisterSchema,
):
    return await user_service.user_register(
        request_body=request_body
    )


@user_router.delete("/{user_uuid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
        user_uuid: Annotated[UUID, Path(description="UUID пользователя")],
        user_service: UserServiceDep,
        _ : Annotated[AppUser, Depends(PermissionChecker(required_permissions=[Permission.USER_DELETE]))]
):
    await user_service.delete_entity_by_uuid(entity_uuid=user_uuid)
