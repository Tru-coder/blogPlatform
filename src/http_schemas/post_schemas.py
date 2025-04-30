from datetime import datetime, timezone
from typing import Annotated, List, Self

from pydantic import Field, field_validator, model_validator

from src.domain.enums.enums import PostStatus
from src.domain.post import Post
from src.domain.tag import Tag
from src.http_schemas.comment_schema import CommentReactionSchema
from src.http_schemas.default_schemas import AppSchema, DefaultSchema
from src.http_schemas.tag_schema import GetTagsSchema
from src.http_schemas.user_schemas import GetUsersSchema


class BasePostSchema(AppSchema):
    title: Annotated[str, Field(
        description='Заголовок поста',
        examples=['Заголовок поста']
    )]
    content: Annotated[str, Field(
        description='Текст поста',
        examples=['Текст поста']
    )]

    category: Annotated[str, Field(
        description='Категория поста',
        examples=['Песочница']
    )]

    status: Annotated[PostStatus, Field(
        examples=PostStatus.all_values()
    )]

    to_published_at: Annotated[datetime | None, Field(
        description="Опубликовать в",
        default=None,
        examples=['2025-01-01T00:00:00Z']
    )]


class GetPostsSchema(DefaultSchema, BasePostSchema):
    views: Annotated[int, Field(
        examples=[10],
        description="Количество просмотров от авторизованных пользователей"
    )]
    pass


class GetPostSchema(GetPostsSchema):
    author: GetUsersSchema
    tags: List[GetTagsSchema]


class GetPostCommentSchema(AppSchema):
    post: GetPostSchema
    comments: List[CommentReactionSchema]


class CreatePostSchema(BasePostSchema):
    tags: Annotated[List[str], Field(
        description='Теги поста',
        examples=[['Космос', 'Астрономия']]
    )]

    def to_orm_model(self, tags: List[Tag]) -> Post:
        return Post(
            title=self.title,
            content=self.content,
            category=self.category,
            status=self.status,
            tags=tags
        )

    @model_validator(mode='after')
    def validate_model_post_status_and_published_at(self) -> Self:
        if self.to_published_at and self.status != PostStatus.DRAFT:
            raise ValueError(
                f"Отложенная публикация постов доступна только постов со статусом {PostStatus.DRAFT.value}"
            )
        return self

    @field_validator('to_published_at')
    @classmethod
    def validate_publish_date(cls, v: datetime | None) -> datetime | None:
        if v is None:
            return v

        if not v.tzinfo:  # если передан наивный datetime
            v = v.replace(tzinfo=timezone.utc)
        else:  # если передан aware datetime, приводим к UTC для сравнения
            v = v.astimezone(timezone.utc)

        if v and v <= datetime.now(timezone.utc):
            raise ValueError("Дата отложенной публикации не может быть в прошлом")
        return v


class UpdatePostSchema(CreatePostSchema):
    title: Annotated[str | None, Field(
        description='Заголовок поста',
        default=None,
        examples=['Заголовок поста']
    )]
    content: Annotated[str | None, Field(
        description='Текст поста',
        default=None,
        examples=['Текст поста']
    )]

    category: Annotated[str | None, Field(
        description='Категория поста',
        default=None,
        examples=['Песочница']
    )]

    status: Annotated[PostStatus | None, Field(
        examples=PostStatus.all_values(),
        default=None,
    )]

    tags: Annotated[List[str] | None, Field(
        description='Теги поста',
        default=None,
        examples=['Космос', 'Астрономия']
    )]

    to_published_at: Annotated[datetime | None, Field(
        description="Опубликовать в",
        default=None,
        examples=['2025-01-01T00:00:00Z']
    )]

    def to_orm_model(self, tags: List[Tag]) -> Post:
        raise NotImplementedError

    @model_validator(mode='after')
    def validate_model(self) -> Self:
        if "title" in self.model_fields_set and self.title is None:
            raise ValueError("Требуется заголовок поста")

        if "content" in self.model_fields_set and self.content is None:
            raise ValueError("Требуется текст поста")

        if "category" in self.model_fields_set and self.category is None:
            raise ValueError("Требуется категория поста")

        if "status" in self.model_fields_set and self.status is None:
            raise ValueError("Требуется статус поста")
        return self
