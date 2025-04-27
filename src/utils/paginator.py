from dataclasses import dataclass

from fastapi import HTTPException, status


@dataclass
class Paginator:
    limit: int = 100
    skip: int = 0

    @staticmethod
    def validate_pagination_param(field: int):
        if field < 0 or field > 1000:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail='Параметры пагинации не могут быть больше 1000 или быть меньше 0')

    def __post_init__(self):
        self.validate_pagination_param(self.limit)
        self.validate_pagination_param(self.skip)
