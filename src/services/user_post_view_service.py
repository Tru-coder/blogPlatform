from typing import List, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from src.database.session_manager import SessionManager
from src.domain.app_user import AppUser
from src.domain.post import Post
from src.domain.user_post_view import UserPostView
from src.repositories.user_post_view_repository import UserPostViewRepository
from src.services.default_service import DefaultService
from src.utils.paginator import Paginator


class UserPostViewService(DefaultService[UserPostView, UserPostViewRepository]):

    def __init__(self, entity_repository: UserPostViewRepository):
        super().__init__(entity_repository)


    async def get_or_create_view_on_post(self, session: AsyncSession, post_id: int, user_id: int) -> UserPostView:
        view = await self.entity_repository.find_view_by_user_id_and_post_id(session=session, user_id=user_id, post_id=post_id)
        if view is None:
            view = await self.entity_repository.add_one(session=session, entity=UserPostView(post_id=post_id, user_id=user_id))
        return view

    @SessionManager.generate_async_transaction(session_kwarg_name='session')
    async def update_views_count_on_posts(self, session: AsyncSession):
      await self.entity_repository.update_views_count_on_posts(session=session)

    @SessionManager.generate_async_transaction(session_kwarg_name='session')
    async def get_viewed_posts(self, session: AsyncSession, current_user: AppUser, paginator: Paginator) -> Tuple[List[Post], int]:
        posts =await  self.entity_repository.find_all_viewed_posts(
            session=session, user_id=current_user.id, paginator=paginator
        )
        total_count = await self.entity_repository.count_query_result(
            session=session, filters={UserPostView.user_id.key: current_user.id}
        )

        return posts, total_count