import os
import shutil
from typing import Union
from fastapi import Depends, Path, Request, BackgroundTasks
from loguru import logger
from fastapi_pagination import Params
from fastapi import APIRouter

from src.config import config
from src.constants.enums import StopAt
from src.crud.task_crud import TaskCrud
from src.db.models import Task
from src.models.exception import HttpException
from src.models.schema import TaskDeletionResponse, TaskQueryResponse, TaskResponse, TaskVideoRequest, SubtitleRequest, \
    AudioRequest
from src.services.task import start
from src.utils import utils

router = APIRouter(tags=["Task"], prefix="/tasks")


def create_task(body: Union[TaskVideoRequest, SubtitleRequest, AudioRequest], stop_at: StopAt):
    task_id = TaskCrud.add_task(stop_at=stop_at, params=body)
    task = {
        "task_id": task_id,
        "params": body.model_dump(),
    }
    logger.success(f"Task created: {utils.to_json(task)}")
    return utils.get_response(200, task)


@router.post("/audio", response_model=TaskResponse, summary="Generate audio task")
def create_audio(body: AudioRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(start, body, StopAt.AUDIO)
    return create_task(body, StopAt.AUDIO)


@router.post("/subtitle", response_model=TaskResponse, summary="Generate audio and subtitle task")
def create_subtitle(body: SubtitleRequest):
    return create_task(body, stop_at=StopAt.SUBTITLE)


@router.post("/videos", response_model=TaskResponse, summary="Generate audio, subtitle and video task")
def create_video(body: TaskVideoRequest):
    return create_task(body, stop_at=StopAt.VIDEO)


@router.get("", response_model=TaskQueryResponse, summary="Get all tasks")
def get_all_tasks(params: Params):
    page = TaskCrud.get_all_tasks(params)
    return utils.get_response(200, page)


@router.get(
    "/{task_id}/status", response_model=TaskQueryResponse, summary="Query task status"
)
def get_task(
    request: Request,
    task_id: str = Path(..., description="Task ID"),
):
    endpoint = config.app.get("endpoint", "")
    if not endpoint:
        endpoint = str(request.base_url)
    endpoint = endpoint.rstrip("/")

    task: Task = TaskCrud.get_task(task_id)
    if task:
        task_dir = utils.task_dir()

        def file_to_uri(file):
            if not file.startswith(endpoint):
                _uri_path = v.replace(task_dir, "tasks").replace("\\", "/")
                _uri_path = f"{endpoint}/{_uri_path}"
            else:
                _uri_path = file
            return _uri_path

        if "videos" in task:
            videos = task["videos"]
            urls = []
            for v in videos:
                urls.append(file_to_uri(v))
            task["videos"] = urls
        if "combined_videos" in task:
            combined_videos = task["combined_videos"]
            urls = []
            for v in combined_videos:
                urls.append(file_to_uri(v))
            task["combined_videos"] = urls
        return utils.get_response(200, task)

    raise HttpException(
        task_id=task_id, status_code=404, message=f"{task_id}: task not found"
    )


@router.delete(
    "/{task_id}",
    response_model=TaskDeletionResponse,
    summary="Delete a generated short video task",
)
def delete_video(task_id: int = Path(..., description="Task ID")):
    task = TaskCrud.get_task(task_id)
    if task:
        tasks_dir = utils.task_dir()
        current_task_dir = os.path.join(tasks_dir, task_id)
        if os.path.exists(current_task_dir):
            shutil.rmtree(current_task_dir)

        TaskCrud.delete_task(task_id)
        logger.success(f"video deleted: {utils.to_json(task)}")
        return utils.get_response(200)

    raise HttpException(
        task_id=task_id, status_code=404, message=f"{task_id}: task not found"
    )
