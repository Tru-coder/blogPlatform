from typing import Annotated, List, Dict

from pydantic import Field, UUID4

from src.domain.comment_reaction import AllowedReactionType
from src.http_schemas.default_schemas import AppSchema, DefaultSchema
from src.http_schemas.user_schemas import GetUsersSchema


class CreateCommentSchema(AppSchema):
    post_uuid: Annotated[UUID4, Field(
        description="UUID поста",
        examples=['748e2d3c-e85f-4599-9efa-4281de612c83'])
    ]
    parent_comment_uuid: Annotated[UUID4 | None, Field(
        default=None,
        description="UUID родительского комментария",
        examples=['748e2d3c-e85f-4599-9efa-4281de612c83'])
    ]
    content: Annotated[str, Field(max_length=512, description="Текст комментария")]

class UpdateCommentSchema(AppSchema):
    content: Annotated[str, Field(max_length=512, min_length=1, description="Текст комментария")]


class GetCommentSchema(DefaultSchema):
    author: Annotated[GetUsersSchema, Field(description="Автор комментария")]
    content: Annotated[str, Field(max_length=512, description="Текст комментария")]

class GetMyCommentSchema(DefaultSchema):
    content: Annotated[str, Field(max_length=512, description="Текст комментария")]
    parent_comment_uuid: Annotated[UUID4 | None, Field(
        default=None,
        description="UUID родительского комментария",
        examples=['748e2d3c-e85f-4599-9efa-4281de612c83'])
    ]

class PutCommentReactionSchema(DefaultSchema):
    reaction_type: Annotated[str, Field(description="Реакция", examples=AllowedReactionType.all_values())]

class CommentPostBaseSchema(GetCommentSchema):
    reactions_count: Annotated[Dict[str, int], Field(description="Реакции на комментарий", default_factory=dict)]


# Альтернативный вариант без пагинации
# class CommentPostSchema(CommentPostBaseSchema):
#     children: Annotated[List['CommentPostSchema'], Field(default_factory=list)]
#
# # Для рекурсивной схемы
# CommentPostSchema.model_rebuild()