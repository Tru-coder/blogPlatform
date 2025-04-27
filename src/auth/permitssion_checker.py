from typing import List, Annotated
from fastapi import status, HTTPException, Depends

from src.auth.permission import Permission
from src.configs.depends import GetCurrentUserDep
from src.domain.app_user import AppUser
from src.logger.app_logger import AppLogger


class PermissionChecker:

    def __init__(self, required_permissions: List[Permission]) -> None:
        self.required_permissions = required_permissions

    async def __call__(self, user: GetCurrentUserDep) -> AppUser:
        for r_perm in self.required_permissions:
            if r_perm.value not in user.get_permissions:
                AppLogger.custom_logger.critical(msg=f"Пользователь={user!r} не имеет разрешения '{r_perm.value}'."
                                                     f"Подозрительная активность")
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

        return user
