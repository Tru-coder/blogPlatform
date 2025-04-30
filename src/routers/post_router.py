from typing import List, Annotated
from uuid import UUID

from fastapi import APIRouter, Response, status, Path, Depends, Query

from src.auth.permission import Permission
from src.auth.permitssion_checker import PermissionChecker
from src.configs.depends import PostServiceDep, PaginatorDep, TimeIntervalDep, GetCurrentOptionalUserDep, \
    CommentServiceDep
from src.domain.app_user import AppUser
from src.domain.comment import Comment
from src.domain.post import PostFiltersUsersParams
from src.http_schemas.post_schemas import GetPostsSchema, CreatePostSchema, UpdatePostSchema, GetPostCommentSchema

post_router = APIRouter(
    prefix="/posts",
    tags=["posts"],
)


async def post_filters(
        tags: Annotated[List[str] | None, Query(description="Список тегов")] = None,
        category: Annotated[str | None, Query(description="Категория")] = None,
        author_uuid: Annotated[UUID | None, Query(description="UUID автора")] = None,
        content: Annotated[str | None, Query(description="Текст поста")] = None
) -> PostFiltersUsersParams:
    return PostFiltersUsersParams(tags=tags, category=category, author_uuid=author_uuid, content=content)


@post_router.get("/", response_model=List[GetPostsSchema])
async def get_published_posts(
        response: Response,
        post_service: PostServiceDep,
        time_interval: TimeIntervalDep,
        paginator: PaginatorDep,
        post_filters_params: PostFiltersUsersParams = Depends(post_filters)
):
    data = await post_service.get_published_posts(
        filters=post_filters_params,
        time_interval=time_interval,
        paginator=paginator
    )

    response.headers["X-Total-Count"] = str(data[1])
    return data[0]


@post_router.get("/{post_uuid}", response_model=GetPostCommentSchema)
async def get_post(
        post_uuid: Annotated[UUID, Path(description="UUID поста")],
        post_service: PostServiceDep,
        comment_service: CommentServiceDep,
        current_user: GetCurrentOptionalUserDep,
        paginator: PaginatorDep,
        response: Response,
):
    data = await post_service.get_post_with_comments(
        post_uuid=post_uuid,
        current_user=current_user,
        paginator=paginator
    )

    comment_count = await  comment_service.count_comments_query(
        filters={Comment.post_id.key: data[0].id, Comment.parent_id.key: None, Comment.is_moderated.key: True}
    )

    response.headers["X-Total-Count"] = str(comment_count)

    return {'post': data[0], 'comments': data[1]}


@post_router.post("/", status_code=status.HTTP_201_CREATED, response_model=GetPostsSchema)
async def create_post(
        post_service: PostServiceDep,
        request_body: CreatePostSchema,
        current_user: AppUser = Depends(
            PermissionChecker([Permission.POST_CREATE])
        )
):
    post = await post_service.create_post(request_body=request_body, current_user=current_user)
    return post


@post_router.patch("/{post_uuid}", response_model=GetPostsSchema)
async def update_post(
        post_uuid: Annotated[UUID, Path(description="UUID поста")],
        post_service: PostServiceDep,
        request_body: UpdatePostSchema,
        current_user: AppUser = Depends(
            PermissionChecker([Permission.POST_UPDATE])
        )
):
    return await post_service.update_post(post_uuid=post_uuid, request_body=request_body, current_user=current_user)


@post_router.delete("/{post_uuid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
        post_uuid: Annotated[UUID, Path(description="UUID поста")],
        post_service: PostServiceDep,
        current_user: AppUser = Depends(
            PermissionChecker([Permission.POST_DELETE])
        )
):
    await post_service.delete_post(post_uuid=post_uuid, current_user=current_user)
