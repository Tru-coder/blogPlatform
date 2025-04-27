from typing import Annotated, Literal

from pydantic import Field, EmailStr, computed_field

from src.domain.app_user import Role
from src.http_schemas.default_schemas import DefaultSchema, AppSchema

class UserPasswordSchema(AppSchema):
    password: Annotated[str, Field(
        description='Пароль пользователя',
        examples=['password']
    )]

class GetUsersSchema(DefaultSchema):
    role_repr: Annotated[str, Field(
        description='Роль пользователя',
        examples=[Role.USER.name, Role.ADMIN.name, Role.AUTHOR.name]
    )]

    login: Annotated[str, Field(
        description='Логин пользователя',
        examples=['author@yandex.ru']
    )]


class UserRegisterSchema(UserPasswordSchema):
    login: Annotated[EmailStr, Field(
        description='Логин пользователя',
        examples=['author@yandex.ru'],
        max_length=64
    )]

    role_value: Annotated[Literal[ "ADMIN", "USER", "AUTHOR"], Field(
        description='Роль пользователя',
        examples=[Role.USER.name, Role.ADMIN.name, Role.AUTHOR.name]
    )]

    @computed_field
    def role(self) -> Role:
        return Role[self.role_value]