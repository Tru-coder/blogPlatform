from typing import Annotated
from uuid import UUID

from pydantic import Field

from src.http_schemas.comment_schema import GetCommentSchema
from src.http_schemas.default_schemas import DefaultSchema


class GetMyReactionsSchema(DefaultSchema):
    reaction_type: Annotated[str, Field(description="Реакция")]
    uuid: Annotated[UUID, Field(description="UUID реакции")]

    comment: GetCommentSchema
