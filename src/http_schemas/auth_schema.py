from typing import Annotated

from pydantic import Field, EmailStr

from src.http_schemas.default_schemas import AppSchema


class UserLogin(AppSchema):
    login: Annotated[EmailStr, Field(
        description="Логин пользователя",
        title="Login",
        max_length=64,
        examples=['author@yandex.ru']
    )]

    password: Annotated[str, Field(
        description="Пароль пользователя",
        title="Password",
        examples=["password"]
    )]
