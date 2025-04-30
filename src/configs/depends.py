from typing import Annotated

from fastapi import Depends

from src.auth.auth_service import AuthService
from src.domain.app_user import AppUser
from src.repositories.comment_reaction_repository import CommentReactionRepository
from src.repositories.comment_repository import CommentRepository
from src.repositories.post_repository import PostRepository
from src.repositories.tag_repository import TagRepository
from src.repositories.user_post_view_repository import UserPostViewRepository
from src.repositories.user_repository import UserRepository
from src.services.comment_reaction_service import CommentReactionService
from src.services.comment_service import CommentService
from src.services.get_post_service import GetPostService
from src.services.post_service import PostService
from src.services.tag_service import TagService
from src.services.user_post_view_service import UserPostViewService
from src.services.user_service import UserService
from src.utils.paginator import Paginator
from src.utils.time_interval import TimeInterval

user_service = UserService(
    entity_repository=UserRepository()
)
tag_service = TagService(
    entity_repository=TagRepository()
)
user_post_view_service = UserPostViewService(
    entity_repository=UserPostViewRepository()
)

auth_service = AuthService(
    user_repository=UserRepository()
)

comment_service = CommentService(
    entity_repository=CommentRepository(),
    get_post_service=GetPostService(
        entity_repository=PostRepository()
    )
)

post_service = PostService(
    entity_repository=PostRepository(),
    tag_service=tag_service,
    user_service=user_service,
    user_post_view_service=user_post_view_service,
    comment_service=comment_service
)

comment_reaction_service = CommentReactionService(
    entity_repository=CommentReactionRepository(),
    comment_service=comment_service
)


def get_tag_service() -> TagService:
    return tag_service


def get_user_service() -> UserService:
    return user_service


def get_post_service() -> PostService:
    return post_service


def get_auth_service() -> AuthService:
    return auth_service


def get_comment_service() -> CommentService:
    return comment_service


def get_comment_reaction_service() -> CommentReactionService:
    return comment_reaction_service


def get_user_post_view_service() -> UserPostViewService:
    return user_post_view_service


TagServiceDep = Annotated[TagService, Depends(get_tag_service)]
UserServiceDep = Annotated[UserService, Depends(get_user_service)]
PostServiceDep = Annotated[PostService, Depends(get_post_service)]
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
UserPostViewServiceDep = Annotated[UserPostViewService, Depends(get_user_post_view_service)]
CommentServiceDep = Annotated[CommentService, Depends(get_comment_service)]
CommentReactionServiceDep = Annotated[CommentReactionService, Depends(get_comment_reaction_service)]

PaginatorDep = Annotated[Paginator, Depends(Paginator)]
TimeIntervalDep = Annotated[TimeInterval, Depends(TimeInterval)]

GetCurrentUserDep = Annotated[AppUser, Depends(get_auth_service().get_current_user)]
GetCurrentOptionalUserDep = Annotated[AppUser | None, Depends(get_auth_service().get_optional_current_user)]
