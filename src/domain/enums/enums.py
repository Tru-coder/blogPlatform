import enum
from typing import List

from src.auth.permission import Permission


@enum.unique
class Role(enum.Enum):
    ADMIN = Permission.admin_permissions()
    USER = Permission.user_permissions()
    AUTHOR = Permission.author_permissions()

    def __str__(self):
        return self.name.lower()

    @classmethod
    def all_values(cls):
        return [role.value for role in cls]


@enum.unique
class AllowedReactionType(enum.Enum):
    THUMB_UP = "👍"
    THUMB_DOWN = "👎"

    LIKE = "❤️"
    JOY = "😂"
    ANGRY = "😡"
    CONFETTI = "🎉"

    @classmethod
    def all_values(cls) -> List[str]:
        return [role.value for role in cls]


@enum.unique
class PostStatus(enum.Enum):
    DRAFT = "черновик"
    PUBLISHED = "опубликован"
    ARCHIVED = "заархивирован"

    @classmethod
    def all_values(cls):
        return [role.value for role in cls]
