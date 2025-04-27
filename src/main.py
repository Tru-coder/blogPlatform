from contextlib import asynccontextmanager
from typing import AsyncGenerator

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.auth.auth_router import auth_router
from src.exceptions.exceptions import DisplayableException
from src.logger.app_logger import AppLogger
from src.redis_tools.redis_tools import RedisTools
from src.routers.comment_router import comment_router
from src.routers.personal_router import personal_router
from src.routers.post_router import post_router
from src.routers.tag_router import tag_router
from src.routers.user_router import user_router


@asynccontextmanager
async def application_lifespan(_: FastAPI) -> AsyncGenerator:
    AppLogger.custom_logger.critical("Starting application lifespan main")

    yield

    AppLogger.custom_logger.critical("Shutting down application lifespan main")
    await RedisTools.disconnect()


app = FastAPI(
    title="Blog Platform API",
    lifespan=application_lifespan
)


@app.exception_handler(DisplayableException)
def business_exception_handler(_: Request, exc: DisplayableException):
    return JSONResponse(status_code=exc.http_status_code, content={"detail": exc.message})


app_routers = [
    auth_router,
    personal_router,
    user_router,
    tag_router,
    post_router,
    comment_router

]

for r in app_routers:
    app.include_router(r, prefix="/api/v1")

if __name__ == "__main__":
    uvicorn.run(
        app='src.main:app',
        host="0.0.0.0",
        port=8002,
        reload=False,
    )
