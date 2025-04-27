from typing import Annotated, List
from uuid import UUID

from fastapi import APIRouter, status, Depends, Path, Response

from src.auth.permission import Permission
from src.auth.permitssion_checker import PermissionChecker
from src.configs.depends import CommentServiceDep, CommentReactionServiceDep, PaginatorDep
from src.domain.app_user import AppUser
from src.domain.comment import Comment
from src.domain.comment_reaction import AllowedReactionType
from src.http_schemas.comment_schema import CreateCommentSchema, GetCommentSchema, PutCommentReactionSchema, \
    CommentPostBaseSchema, UpdateCommentSchema

comment_router = APIRouter(
    prefix="/comments",
    tags=["comments"],
)


@comment_router.get("/to-moderate", response_model=List[GetCommentSchema])
async def get_to_moderate_comments(
        response: Response,
        comment_service: CommentServiceDep,
        paginator: PaginatorDep,
        _: AppUser = Depends(
            PermissionChecker(
                required_permissions=[Permission.COMMENT_TO_MODERATE]
            )
        )
):
    total_count = await comment_service.count_comments_query(filters={Comment.is_moderated.key: False})
    response.headers["X-Total-Count"] = str(total_count)
    return await comment_service.get_to_moderate_comments(paginator=paginator)


@comment_router.post("/", response_model=GetCommentSchema, status_code=status.HTTP_201_CREATED)
async def create_comment(
        comment_service: CommentServiceDep,
        request_body: CreateCommentSchema,
        current_user: AppUser = Depends(
            PermissionChecker(
                required_permissions=[Permission.COMMENT_CREATE]
            )
        )
):
    return await comment_service.create_comment(
        request_body=request_body,
        current_user=current_user
    )


@comment_router.get("/{comment_uuid}", response_model=CommentPostBaseSchema)
async def get_comment(
        comment_uuid: Annotated[UUID, Path(description="UUID комментария")],
        comment_service: CommentServiceDep
):
    return await comment_service.get_comment_with_reactions(comment_uuid=comment_uuid)


@comment_router.get("/{comment_uuid}/children", response_model=List[CommentPostBaseSchema])
async def get_children_comments(
        response: Response,
        comment_uuid: Annotated[UUID, Path(description="UUID родительского комментария")],
        comment_service: CommentServiceDep,
        paginator: PaginatorDep
):
    data = await comment_service.get_children_comments(
        comment_uuid=comment_uuid, paginator=paginator
    )
    response.headers["X-Total-Count"] = str(data[1])
    return data[0]


@comment_router.patch("/{comment_uuid}", response_model=GetCommentSchema)
async def update_comment(
        comment_uuid: Annotated[UUID, Path(description="UUID комментария")],
        comment_service: CommentServiceDep,
        request_body: UpdateCommentSchema,
        current_user: AppUser = Depends(
            PermissionChecker(
                required_permissions=[Permission.COMMENT_UPDATE]
            )
        )
):
    return await comment_service.update_comment(comment_uuid=comment_uuid, request_body=request_body,
                                                current_user=current_user)


@comment_router.patch("/{comment_uuid}/moderate", response_model=GetCommentSchema)
async def moderate_comment(
        comment_uuid: Annotated[UUID, Path(description="UUID комментария")],
        comment_service: CommentServiceDep,
        _: AppUser = Depends(
            PermissionChecker(
                required_permissions=[Permission.COMMENT_MODERATE]
            )
        )
):
    return await comment_service.moderate_comment(comment_uuid=comment_uuid)


@comment_router.delete("/{comment_uuid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
        comment_uuid: Annotated[UUID, Path(description="UUID комментария")],
        comment_service: CommentServiceDep,
        current_user: AppUser = Depends(
            PermissionChecker(
                required_permissions=[Permission.COMMENT_DELETE]
            )
        )
):
    await comment_service.delete_comment(comment_uuid=comment_uuid, current_user=current_user)


@comment_router.put("{comment_uuid}/reactions/{reaction}", response_model=PutCommentReactionSchema)
async def put_reaction(
        reaction: AllowedReactionType,
        comment_uuid: Annotated[UUID, Path(description="UUID комментария")],
        comment_reaction_service: CommentReactionServiceDep,
        current_user: AppUser = Depends(
            PermissionChecker(
                required_permissions=[Permission.COMMENT_REACT]
            )
        )
):
    return await comment_reaction_service.put_reaction(
        comment_uuid=comment_uuid, reaction=reaction,
        current_user=current_user)


@comment_router.delete("/reactions/{reaction_uuid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reaction(
        reaction_uuid: Annotated[UUID, Path(description="UUID реакции")],
        comment_reaction_service: CommentReactionServiceDep,
        current_user: AppUser = Depends(
            PermissionChecker(
                required_permissions=[Permission.COMMENT_REACT_DELETE]
            )
        )
):
    await comment_reaction_service.delete_reaction(reaction_uuid=reaction_uuid, current_user=current_user)
