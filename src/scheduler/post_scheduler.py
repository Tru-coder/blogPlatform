from typing import TypedDict, Type

from arq import cron, run_worker
from arq.typing import WorkerSettingsBase

from src.logger.app_logger import AppLogger
from src.redis_tools.redis_tools import RedisTools
from src.repositories.comment_repository import CommentRepository
from src.repositories.post_repository import PostRepository
from src.repositories.tag_repository import TagRepository
from src.repositories.user_post_view_repository import UserPostViewRepository
from src.repositories.user_repository import UserRepository
from src.services.comment_service import CommentService
from src.services.get_post_service import GetPostService
from src.services.post_service import PostService
from src.services.tag_service import TagService
from src.services.user_post_view_service import UserPostViewService
from src.services.user_service import UserService


class ContextDict(TypedDict):
    redis_client: Type[RedisTools]
    post_service: PostService
    user_post_view_service: UserPostViewService


async def startup(ctx: ContextDict):
    user_post_view_service = UserPostViewService(entity_repository=UserPostViewRepository())
    post_service = PostService(
        entity_repository=PostRepository(),
        tag_service=TagService(entity_repository=TagRepository()),
        user_service=UserService(entity_repository=UserRepository()),
        user_post_view_service=user_post_view_service,
        comment_service=CommentService(entity_repository=CommentRepository(), get_post_service=GetPostService(
            entity_repository=PostRepository()
        ))
    )

    ctx['redis_client'] = RedisTools
    ctx['post_service'] = post_service
    ctx['user_post_view_service'] = user_post_view_service


async def shutdown(ctx: ContextDict):
    await ctx['redis_client'].disconnect()


async def publish_postponed_posts(ctx: ContextDict):
    published_posts = await ctx['post_service'].publish_postpone_posts()
    AppLogger.custom_logger.info(f'Опубликованные посты={published_posts}')


async def update_post_views_count(ctx: ContextDict):
    await ctx['user_post_view_service'].update_views_count_on_posts()
    AppLogger.custom_logger.info(f'Обновляю счётчики-количества просмотров постов')


class WorkerSettings(WorkerSettingsBase):
    redis_settings = RedisTools.scheduler_settings()
    on_startup = startup
    on_shutdown = shutdown
    cron_jobs = [
        cron(coroutine=publish_postponed_posts, second=0),  # every minute
        cron(coroutine=update_post_views_count, second=0),  # every minute
    ]


if __name__ == "__main__":
    AppLogger.custom_logger.critical('Post Scheduler initialized')
    run_worker(WorkerSettings)
