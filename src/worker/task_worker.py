import asyncio
from tembo_pgmq_python import Message
from loguru import logger

from src.constants.consts import TASK_QUEUE_NAME
from src.constants.enums import StopAt
from src.crud.task_crud import TaskCrud
from src.db.connection import pgmq
from src.db.models import Task
from src.models.schema import AudioRequest, VideoRequest, SubtitleRequest
from src.services.task_service import TaskService

task_service = TaskService()
task_crud = TaskCrud()

async def consume_messages():
    while True:
        msg: Message = pgmq.read(TASK_QUEUE_NAME)
        if msg:
            logger.info(f"Processing message {msg.msg_id}")
            process_task(msg)
            pgmq.delete(TASK_QUEUE_NAME, msg.msg_id)
            logger.info(f"Processed message {msg.msg_id}")
        else:
            await asyncio.sleep(2)


def process_task(message: Message):
    task_id = message.message.get("task_id")
    if not task_id:
        logger.error("No task_id in message queue")
        return

    task: Task = task_crud.get_task(task_id)
    stop_at = StopAt(task.stop_at)
    request = VideoRequest
    if stop_at == StopAt.AUDIO:
        request = AudioRequest
    elif stop_at == StopAt.SUBTITLE:
        request = SubtitleRequest
    params = request(**task.params)

    task_service.start(task.id, params, stop_at)

