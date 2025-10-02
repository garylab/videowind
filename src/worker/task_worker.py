import asyncio
from loguru import logger

from src.constants.consts import TASK_QUEUE_NAME
from src.constants.enums import StopAt
from src.crud.task_crud import TaskCrud
from src.db.models import Task
from src.models.schema import AudioRequest, VideoRequest, SubtitleRequest
from src.services.task_service import TaskService
from src.services.queue_service import QueueService, QueueMessage

task_service = TaskService()
task_crud = TaskCrud()

async def consume_messages():
    while True:
        msg: QueueMessage = QueueService.read(TASK_QUEUE_NAME)
        if msg:
            logger.info(f"Processing message {msg.msg_id}")
            try:
                process_task(msg)
                QueueService.delete(TASK_QUEUE_NAME, msg.msg_id)
                logger.info(f"Processed message {msg.msg_id}")
            except Exception as e:
                logger.error(f"Failed to process message {msg.msg_id}: {e}")
                QueueService.retry_message(TASK_QUEUE_NAME, msg.msg_id)
        else:
            await asyncio.sleep(2)


def process_task(message: QueueMessage):
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

