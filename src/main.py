import asyncio
import os
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger
import uvicorn

from src.controllers import ping_router
from src.controllers.exception_handlers import exception_handler, validation_exception_handler
from src.controllers.v1 import llm_router, task_router, music_router, download_router, voice_router
from src.db.connection import engine, create_tables
from src.models.exception import HttpException
from src.utils import utils
from src.constants.config import env
from src.worker.task_worker import consume_messages

stop_event = asyncio.Event()
background_tasks: List[asyncio.Task] = []

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    background_tasks.append(asyncio.create_task(consume_messages()))
    logger.info("started lifespan")

    yield

    for task in background_tasks:
        task.cancel()
    if background_tasks:
        await asyncio.gather(*background_tasks, return_exceptions=True)

    engine.dispose()
    logger.info("ended lifespan")

app = FastAPI(
    title=env.APP.name,
    description=env.APP.description,
    version=env.APP.version,
    debug=env.APP.debug_mode,
    lifespan=lifespan
)
app.include_router(ping_router.router)
app.include_router(task_router.router)
app.include_router(llm_router.router)
app.include_router(voice_router.router)
app.include_router(music_router.router)
app.include_router(download_router.router)


app.add_exception_handler(HttpException, exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)


# Configures the CORS middleware for the FastAPI app
cors_allowed_origins_str = os.getenv("CORS_ALLOWED_ORIGINS", "")
origins = cors_allowed_origins_str.split(",") if cors_allowed_origins_str else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

task_dir = utils.task_dir()
app.mount(
    "/tasks", StaticFiles(directory=task_dir, html=True, follow_symlink=True), name=""
)

public_dir = utils.public_dir()
app.mount("/", StaticFiles(directory=public_dir, html=True), name="")


if __name__ == "__main__":
    logger.info(f"start server, docs: http://{env.APP.host}:{env.APP.port}/docs")
    uvicorn.run(
        app="src.main:app",
        host=env.APP.host,
        port=env.APP.port,
        reload=env.APP.reload,
        log_level=env.APP.log_level,
    )
