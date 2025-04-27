from typing import Annotated

from fastapi import APIRouter, status, HTTPException, Cookie
from fastapi.responses import JSONResponse

from src.configs.depends import AuthServiceDep, GetCurrentUserDep, UserServiceDep
from src.http_schemas.auth_schema import UserLogin
from src.http_schemas.user_schemas import GetUsersSchema, UserPasswordSchema

auth_router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)


@auth_router.post("/login", )
async def login(
        auth_service: AuthServiceDep,
        request_body: UserLogin,
):
    content = await auth_service.login_user(request_body=request_body)
    response = JSONResponse(
        content={"message": "OK"},
        status_code=status.HTTP_200_OK
    )
    response.set_cookie(
        key="access_token",
        expires=content.access_token_expired_at,
        path="/",
        value=content.access_token,
        httponly=True,
        samesite='strict',
        secure=False
    )
    response.set_cookie(
        key="refresh_token",
        expires=content.refresh_token_expired_at,
        path="/",
        value=content.refresh_token,
        httponly=True,
        samesite='strict',
        secure=False
    )

    return response


@auth_router.post("/logout", summary="Logout")
async def logout(
        auth_service: AuthServiceDep,
        user_refresh_token: Annotated[str | None, Cookie(alias="refresh_token")] = None,
):
    if user_refresh_token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    await auth_service.logout(refresh_token=user_refresh_token)

    response = JSONResponse(
        content={"message": "OK"},
        status_code=status.HTTP_200_OK
    )
    response.delete_cookie(
        key="access_token",
        path="/",
        httponly=True,
        samesite='strict',
        secure=True
    )
    response.delete_cookie(
        key="refresh_token",
        path="/",
        httponly=True,
        samesite='strict',
        secure=True
    )
    return response


@auth_router.post("/refresh-token", summary="Refresh token")
async def refresh_token(
        auth_service: AuthServiceDep,
        jwt_refresh_token: Annotated[str | None, Cookie(alias="refresh_token")] = None,
):
    if jwt_refresh_token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    content = await auth_service.refresh_user_tokens(token=jwt_refresh_token)

    response = JSONResponse(
        content={"message": "OK"},
        status_code=status.HTTP_200_OK
    )

    response.set_cookie(
        key="access_token",
        expires=content[1],
        path="/",
        value=content[0],
        httponly=True,
        samesite='strict',
        secure=True
    )

    return response


@auth_router.get('/me', response_model=GetUsersSchema)
async def get_me(
        current_user: GetCurrentUserDep
):
    return current_user


@auth_router.patch("/me/reset-password", response_model=GetUsersSchema)
async def update_password(
        user_service: UserServiceDep,
        request_body: UserPasswordSchema,
        current_user: GetCurrentUserDep
):
    return await user_service.update_password(user_uuid=current_user.uuid, request_body=request_body)
