from typing import Annotated

from pydantic import Field

from src.http_schemas.default_schemas import AppSchema, DefaultSchema


class CreateTagSchema(AppSchema):
    name: Annotated[str, Field(
        description="Название тега",
        examples=['Научная фантастика'],
        max_length=64
    )]

class GetTagsSchema(CreateTagSchema, DefaultSchema):
    pass

class UpdateTagSchema(CreateTagSchema):
    pass