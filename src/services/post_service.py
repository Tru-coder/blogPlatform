from typing import List, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.database.session_manager import SessionManager
from src.domain.app_user import AppUser
from src.domain.enums.enums import Role, PostStatus
from src.domain.post import Post, PostFiltersUsersParams, PostFiltersParams
from src.domain.user_post_view import UserPostView
from src.exceptions.post_exceptions import PostNotFoundException
from src.http_schemas.post_schemas import CreatePostSchema, UpdatePostSchema
from src.repositories.post_repository import PostRepository
from src.services.comment_service import CommentService, CommentReactionsModel
from src.services.default_service import DefaultService
from src.services.tag_service import TagService
from src.services.user_post_view_service import UserPostViewService
from src.services.user_service import UserService
from src.utils.paginator import Paginator
from src.utils.time_interval import TimeInterval


class PostService(DefaultService[Post, PostRepository]):
    entity_not_found_exception = PostNotFoundException

    def __init__(
            self,
            entity_repository: PostRepository,
            tag_service: TagService, user_service: UserService,
            user_post_view_service: UserPostViewService,
            comment_service: CommentService
    ) -> None:
        super().__init__(entity_repository)
        self.tag_service = tag_service
        self.user_service = user_service
        self.user_post_view_service = user_post_view_service
        self.comment_service = comment_service

    @SessionManager.generate_async_transaction(session_kwarg_name="session")
    async def create_post(self, session: AsyncSession, request_body: CreatePostSchema, current_user: AppUser) -> Post:
        post_tags = [await self.tag_service.get_tag_by_name(session=session, name=i) for i in request_body.tags]

        post = request_body.to_orm_model(tags=post_tags)
        post.author_id = current_user.id
        return await self.entity_repository.add_one(
            session=session,
            entity=post
        )

    @SessionManager.generate_async_transaction(session_kwarg_name="session")
    async def update_post(
            self,
            session: AsyncSession,
            request_body: UpdatePostSchema,
            post_uuid: UUID,
            current_user: AppUser
    ) -> Post:
        to_update_data = request_body.model_dump(exclude_unset=True)

        if request_body.tags:
            post_tags = [await self.tag_service.get_tag_by_name(session=session, name=i) for i in request_body.tags]
            to_update_data['tags'] = post_tags

        return self.update_entity(
            entity=await self.get_post_with_tags_and_author(session=session, post_uuid=post_uuid, author=current_user),
            new_values=to_update_data
        )

    async def get_post_with_tags_and_author(self, session: AsyncSession, post_uuid: UUID, author: AppUser) -> Post:
        existed_post = await self.entity_repository.find_post_with_tags_and_author(
            session=session, post_uuid=post_uuid, author_id=author.id
        )
        if existed_post is None:
            raise self.entity_not_found_exception(f"Пост с uuid {post_uuid} не найден")

        return existed_post

    @SessionManager.generate_async_transaction(session_kwarg_name="session")
    async def get_published_posts(
            self, session: AsyncSession, paginator: Paginator, time_interval: TimeInterval,
            filters: PostFiltersUsersParams
    ) -> Tuple[List[Post], int]:
        filters['tags'] = filters['tags'] if filters['tags'] else []

        post_filters = PostFiltersParams(
            author_id=(
                await self.user_service.get_entity_by_uuid(session=session, entity_uuid=filters["author_uuid"])).id if
            filters["author_uuid"] is not None else None,
            category=filters["category"],
            content=filters["content"],
            tags=[(await self.tag_service.get_tag_by_name(session=session, name=i)).id for i in filters["tags"]]
        )
        return (
            await self.entity_repository.find_published_posts(
                session=session,
                paginator=paginator,
                time_interval=time_interval,
                filters=post_filters
            ),
            await self.entity_repository.count_query_find_published_posts(
                session=session,
                filters=post_filters,
                time_interval=time_interval
            )
        )

    async def view_post(self, session: AsyncSession, post: Post, current_user: AppUser | None) -> UserPostView | None:
        if current_user:
            return await self.user_post_view_service.get_or_create_view_on_post(
                session=session, post_id=post.id, user_id=current_user.id
            )
        return None

    @SessionManager.generate_async_transaction(session_kwarg_name="session")
    async def get_post_with_comments(
            self, session: AsyncSession,
            post_uuid: UUID,
            current_user: AppUser | None,
            paginator: Paginator
    ) -> Tuple[Post, List[CommentReactionsModel]]:
        post = await self.get_post_with_author_and_tags(session=session, post_uuid=post_uuid)

        await self.view_post(session=session, post=post, current_user=current_user)

        comments = await self.comment_service.get_root_comments_for_post(
            session=session, post_id=post.id, paginator=paginator
        )

        return post, comments

    async def get_post_with_author_and_tags(self, session: AsyncSession, post_uuid: UUID) -> Post:

        post = await self.entity_repository.find_post_with_author_and_tags(
            session=session, post_uuid=post_uuid
        )
        if post is None:
            raise self.entity_not_found_exception(f"<Post(uuid={post_uuid})> не найден")

        return post

    @SessionManager.generate_async_transaction(session_kwarg_name="session")
    async def publish_postpone_posts(self, session: AsyncSession) -> List[Post]:
        to_publish_posts = await self.entity_repository.find_posts_to_publish(
            session=session
        )
        for i in to_publish_posts:
            i.status = PostStatus.PUBLISHED
            i.to_published_at = None

        return to_publish_posts

    @SessionManager.generate_async_transaction(session_kwarg_name="session")
    async def delete_post(self, session: AsyncSession, post_uuid: UUID, current_user: AppUser) -> None:
        if current_user.role == Role.ADMIN:
            await self.entity_repository.delete_all_data_with_filter(session=session, filters={"uuid": post_uuid})

        await self.entity_repository.delete_all_data_with_filter(session=session, filters={Post.uuid.key: post_uuid,
                                                                                           Post.author_id.key: current_user.id})

    @SessionManager.generate_async_transaction(session_kwarg_name="session")
    async def get_my_posts(self, session: AsyncSession, current_user: AppUser, paginator: Paginator) -> [List[Post],
                                                                                                         int]:
        posts = await self.entity_repository.find_all_with_filters(
            session=session,
            filters={Post.author_id.key: current_user.id},
            paginator=paginator
        )

        count = await self.entity_repository.count_query_find_all(
            session=session,
            filters={Post.author_id.key: current_user.id}
        )

        return posts, count
