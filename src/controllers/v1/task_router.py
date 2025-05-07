import os
import shutil
from fastapi import Depends, Path, Request, BackgroundTasks
from loguru import logger
from fastapi_pagination import Params, Page
from fastapi import APIRouter

from src.constants.enums import StopAt
from src.crud.task_crud import TaskCrud
from src.db.models import Task
from src.models.exception import HttpException
from src.models.schema import TaskDeletionResponse, TaskIdOut, SubtitleRequest, \
    AudioRequest, TaskStatusOut, TaskOut, TaskLiteOut, VideoRequest
from src.services.task_service import TaskService
from src.utils import utils

router = APIRouter(tags=["Task"], prefix="/tasks")
task_service = TaskService()


@router.post("/audio", response_model=TaskIdOut, summary="Generate audio task")
def create_audio(body: AudioRequest, background_tasks: BackgroundTasks):
    task_id = TaskCrud.add_task(params=body, stop_at=StopAt.AUDIO)
    background_tasks.add_task(task_service.start, task_id, body, StopAt.AUDIO)
    return TaskIdOut(task_id=task_id)


@router.post("/subtitle", response_model=TaskIdOut, summary="Generate audio and subtitle task")
def create_subtitle(body: SubtitleRequest, background_tasks: BackgroundTasks):
    task_id = TaskCrud.add_task(params=body, stop_at=StopAt.SUBTITLE)
    background_tasks.add_task(task_service.start, task_id, body, StopAt.SUBTITLE)
    return TaskIdOut(task_id=task_id)


@router.post("/videos", response_model=TaskIdOut, summary="Generate audio, subtitle and video task")
def create_video(body: VideoRequest, background_tasks: BackgroundTasks):
    task_id = TaskCrud.add_task(params=body, stop_at=StopAt.VIDEO)
    background_tasks.add_task(task_service.start, task_id, body, StopAt.VIDEO)
    return TaskIdOut(task_id=task_id)


@router.get("", response_model=Page[TaskLiteOut], summary="Get all tasks")
def get_all_tasks(params: Params = Depends()):
    page: Page[Task] = TaskCrud.get_all_tasks(params)
    page.items = [TaskLiteOut.model_validate(task) for task in page.items]
    return page


@router.get("/{task_id}", response_model=TaskOut, summary="Query task")
def get_task(
    task_id: str = Path(..., description="Task ID"),
):
    task: Task = TaskCrud.get_task(task_id)
    if not task:
        raise HttpException(
            task_id=task_id, status_code=404, message=f"{task_id}: task not found"
        )

    return TaskOut.model_validate(task)

@router.get("/{task_id}/status", response_model=TaskStatusOut, summary="Query task status")
def get_task_status(
        request: Request,
        task_id: str = Path(..., description="Task ID"),
):
    task: Task = TaskCrud.get_task(task_id)
    if not task:
        raise HttpException(
            task_id=task_id, status_code=404, message=f"{task_id}: task not found"
        )

    return TaskStatusOut(task_id=task_id, status=task.status)


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
