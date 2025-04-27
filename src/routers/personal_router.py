from typing import List

from fastapi import APIRouter
from fastapi import Response

from src.configs.depends import PostServiceDep, PaginatorDep, CommentServiceDep, \
    GetCurrentUserDep, CommentReactionServiceDep, UserPostViewServiceDep
from src.http_schemas.comment_reactions_schema import GetMyReactionsSchema
from src.http_schemas.comment_schema import GetMyCommentSchema, CommentPostBaseSchema
from src.http_schemas.post_schemas import GetPostsSchema

personal_router = APIRouter(
    prefix="/personal",
    tags=["personal"],
)


@personal_router.get("/my-posts", response_model=List[GetPostsSchema])
async def get_my_posts(
        response: Response,
        paginator: PaginatorDep,
        post_service: PostServiceDep,
        current_user: GetCurrentUserDep,
):
    data = await post_service.get_my_posts(current_user=current_user, paginator=paginator)
    response.headers["X-Total-Count"] = str(data[1])
    return data[0]


@personal_router.get("/my-comments", response_model=List[GetMyCommentSchema])
async def get_my_comments(
        response: Response,
        paginator: PaginatorDep,
        comment_service: CommentServiceDep,
        current_user: GetCurrentUserDep,
):
    data = await comment_service.get_my_comments(current_user=current_user, paginator=paginator)
    response.headers["X-Total-Count"] = str(data[1])
    return data[0]


@personal_router.get("/my-reactions", response_model=List[GetMyReactionsSchema])
async def get_my_reactions(
        response: Response,
        paginator: PaginatorDep,
        reaction_service: CommentReactionServiceDep,
        current_user: GetCurrentUserDep,
):
    data = await reaction_service.get_my_reactions(current_user=current_user, paginator=paginator)
    response.headers["X-Total-Count"] = str(data[1])
    return data[0]

@personal_router.get("/viewed-posts", response_model=List[GetPostsSchema])
async def get_viewed_posts(
        response: Response,
        view_service: UserPostViewServiceDep,
        current_user: GetCurrentUserDep,
        paginator: PaginatorDep
):

    data = await view_service.get_viewed_posts(current_user=current_user, paginator=paginator)
    response.headers["X-Total-Count"] = str(data[1])
    return data[0]