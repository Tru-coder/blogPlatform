import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class AppSchema(BaseModel):
    model_config = ConfigDict(extra='forbid')

class DefaultSchema(BaseModel):
    uuid: Annotated[UUID, Field(
        description='UUID',
        examples=['748e2d3c-e85f-4599-9efa-4281de612c83']
    )]

    created_at: Annotated[datetime.datetime, Field(
        description='Дата создания',
        examples=['2023-01-01T00:00:00']
    )]
