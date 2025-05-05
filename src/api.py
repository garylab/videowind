import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger
import uvicorn

from src.controllers.exception_handlers import exception_handler, validation_exception_handler
from src.controllers.v1 import video_router, llm_router
from src.models.exception import HttpException
from src.utils import utils
from src.constants.config import AppConfig

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("start lifespan")
    yield
    logger.info("end lifespan")

app = FastAPI(
    title=AppConfig.name,
    description=AppConfig.description,
    version=AppConfig.version,
    debug=AppConfig.debug_mode,
    lifespan=lifespan
)
app.include_router(video_router.router)
app.include_router(llm_router.router)
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
    logger.info(f"start server, docs: http://{AppConfig.host}:{AppConfig.port}/docs")
    uvicorn.run(
        app="src.api:app",
        host=AppConfig.host,
        port=AppConfig.port,
        reload=AppConfig.reload,
        log_level="warning",
    )
