from dataclasses import dataclass
from typing import Any, List, Tuple, Dict
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession


from src.database.session_manager import SessionManager
from src.domain.app_user import AppUser
from src.domain.enums.enums import Role, PostStatus
from src.domain.comment import Comment
from src.domain.post import Post
from src.exceptions.comment_exceptions import CommentNotFoundException
from src.http_schemas.comment_schema import CreateCommentSchema, UpdateCommentSchema
from src.repositories.comment_repository import CommentRepository
from src.services.default_service import DefaultService
from src.services.get_post_service import GetPostService
from src.utils.paginator import Paginator

@dataclass
class  CommentReactionsModel:
    comment: Comment
    reactions_count: Dict[str, int]

class CommentService(DefaultService[Comment, CommentRepository]):
    entity_not_found_exception = CommentNotFoundException

    def __init__(self, entity_repository: CommentRepository, get_post_service: GetPostService):
        super().__init__(entity_repository)
        self.get_post_service = get_post_service

    @SessionManager.generate_async_transaction(session_kwarg_name="session")
    async def get_comment_with_author(self, session: AsyncSession, comment_uuid: UUID) -> Comment:
        existed_comment = await self.entity_repository.find_comment_with_author(
            session=session, comment_uuid=comment_uuid
        )
        if existed_comment is None:
            raise self.entity_not_found_exception(f"Комментарий с uuid {comment_uuid} не найден")

        return existed_comment

    async def get_comment_with_author_by_user(self, session: AsyncSession, comment_uuid: UUID, current_user: AppUser) -> Comment:
        existed_comment = await self.entity_repository.get_comment_with_author_and_filters(
            session=session, filters={Comment.uuid.key: comment_uuid, Comment.author_id.key: current_user.id}
        )
        if existed_comment is None:
            raise self.entity_not_found_exception(f"Комментарий с uuid {comment_uuid} не найден или не принадлежит пользователю {current_user!r}")

        return existed_comment

    async def get_comment_with_author_and_filters(self, session: AsyncSession, filters: dict[str, Any]) -> Comment:
        existed_comment = await self.entity_repository.get_comment_with_author_and_filters(
            session=session,
            filters=filters
        )

        if existed_comment is None:
            raise self.entity_not_found_exception(f"Комментарий с {str(filters)} не найден")

        return existed_comment

    @SessionManager.generate_async_transaction(session_kwarg_name="session")
    async def create_comment(
            self, session: AsyncSession, request_body: CreateCommentSchema, current_user: AppUser
    ) -> Comment:
        post = await self.get_post_service.get_one_with_filters(
            session=session,
            filters={Post.uuid.key: request_body.post_uuid, Post.status.key: PostStatus.PUBLISHED}
        )
        parent_comment = await self.get_entity_by_uuid(session=session, entity_uuid=request_body.parent_comment_uuid) \
            if request_body.parent_comment_uuid else None

        comment = Comment(
            content=request_body.content,
            author=current_user,
            post_id=post.id,
            parent_id=parent_comment.id if parent_comment else None
        )

        return await self.create_entity(
            session=session,
            entity=comment
        )

    @SessionManager.generate_async_transaction(session_kwarg_name="session")
    async def moderate_comment(self, session: AsyncSession, comment_uuid: UUID) -> Comment:
        comment = await self.get_comment_with_author(session=session, comment_uuid=comment_uuid)
        comment.is_moderated = True
        return comment

    async def get_root_comments_for_post(
            self, session: AsyncSession, post_id: int, paginator: Paginator
    ) -> List[CommentReactionsModel]:
        comments = await self.entity_repository.find_root_comments_for_post(
            session=session, post_id=post_id, paginator=paginator
        )

        comments = await self.set_comments_ggg_reactions(session, comments)

        return comments

    @SessionManager.generate_async_transaction(session_kwarg_name='session')
    async def get_children_comments(self, session: AsyncSession, comment_uuid: UUID, paginator: Paginator)\
            -> tuple[ List[CommentReactionsModel], int]:
        parent_comment = await self.get_entity_by_uuid(session=session, entity_uuid=comment_uuid)
        comments = await self.entity_repository.find_children_comments(
            session=session, parend_comment_id=parent_comment.id, paginator=paginator
        )
        comments = await self.set_comments_ggg_reactions(session, comments)

        total_count = await self.count_comments_query(
            session=session,
            filters={Comment.parent_id.key: parent_comment.id, Comment.is_moderated.key: True}
        )
        return comments, total_count

    async def set_comments_ggg_reactions(self, session: AsyncSession, comments: List[Comment]) -> List[CommentReactionsModel]:
        # Загрузка реакций для комментариев
        comment_ids = [c.id for c in comments]

        reactions_dict = await  self.entity_repository.load_reactions_for_comments(
            session=session, comment_ids=comment_ids
        )

        return [
            CommentReactionsModel(comment=comment, reactions_count=reactions_dict.get(comment.id, {}))
            for comment in comments
        ]

    @SessionManager.generate_async_transaction(session_kwarg_name='session')
    async def count_comments_query(self, session: AsyncSession, filters: dict[str, Any]) -> int:
        return await self.entity_repository.count_comments_query(session=session, filters=filters)

    @SessionManager.generate_async_transaction(session_kwarg_name='session')
    async def get_to_moderate_comments(self, session: AsyncSession, paginator: Paginator) -> List[Comment]:
        return await self.entity_repository.find_to_moderate_comments(session=session, paginator=paginator)

    @SessionManager.generate_async_transaction(session_kwarg_name='session')
    async def delete_comment(self, session: AsyncSession, comment_uuid: UUID, current_user: AppUser) -> None:
        if current_user.role == Role.ADMIN:
            await self.entity_repository.delete_all_data_with_filter(session=session, filters={"uuid": comment_uuid})

        await self.entity_repository.delete_all_data_with_filter(session=session, filters={Comment.uuid.key: comment_uuid, Comment.author_id.key: current_user.id})

    @SessionManager.generate_async_transaction(session_kwarg_name='session')
    async def update_comment(self, session: AsyncSession, comment_uuid: UUID, request_body: UpdateCommentSchema, current_user: AppUser) -> Comment:
        comment = await self.get_comment_with_author_by_user(session=session, comment_uuid=comment_uuid, current_user=current_user)
        comment.content = request_body.content
        comment.is_moderated = False
        return comment

    @SessionManager.generate_async_transaction(session_kwarg_name='session')
    async def get_my_comments(self, session: AsyncSession, current_user: AppUser, paginator: Paginator) -> Tuple[List[Comment], int]:
        comments =  await self.entity_repository.find_all_with_filters(session=session, filters={Comment.author_id.key: current_user.id}, paginator=paginator)
        total_count = await self.count_comments_query(session=session, filters={Comment.author_id.key: current_user.id})

        return comments, total_count

    @SessionManager.generate_async_transaction(session_kwarg_name='session')
    async def get_comment_with_reactions(self, session: AsyncSession, comment_uuid: UUID) -> CommentReactionsModel:
        comment = await self.get_comment_with_author(session=session, comment_uuid=comment_uuid)
        reactions_count = await self.entity_repository.load_reactions_for_comments(session=session, comment_ids=[comment.id])
        return CommentReactionsModel(
            comment=comment,
            reactions_count=reactions_count.get(comment.id, {})
        )