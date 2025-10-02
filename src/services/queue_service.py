from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_
from loguru import logger
from uuid6 import uuid7

from src.db.connection import SessionLocal
from src.db.models import TaskQueue
from src.utils.date_utils import get_now


class QueueService:
    """Database-based queue service to replace pgmq functionality"""
    
    @staticmethod
    def send(queue_name: str, message: Dict[str, Any]) -> str:
        """Add a message to the queue"""
        db: Session = SessionLocal()
        try:
            task_id = message.get("task_id")
            if not task_id:
                raise ValueError("Message must contain 'task_id'")
            
            queue_item = TaskQueue(
                task_id=task_id,
                message=message,
                processed=False,
                retry_count=0
            )
            
            db.add(queue_item)
            db.commit()
            db.refresh(queue_item)
            
            logger.info(f"Added message to queue: {queue_item.id} for task: {task_id}")
            return str(queue_item.id)
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to send message to queue: {e}")
            raise
        finally:
            db.close()
    
    @staticmethod
    def read(queue_name: str) -> Optional['QueueMessage']:
        """Read and lock the next unprocessed message from the queue"""
        db: Session = SessionLocal()
        try:
            # Get the oldest unprocessed message
            queue_item = db.query(TaskQueue).filter(
                and_(
                    TaskQueue.processed == False,
                    TaskQueue.retry_count < TaskQueue.max_retries
                )
            ).order_by(TaskQueue.created_at.asc()).first()
            
            if queue_item:
                # Mark as being processed
                queue_item.processing_started_at = get_now()
                db.commit()
                
                return QueueMessage(
                    msg_id=str(queue_item.id),
                    message=queue_item.message,
                    retry_count=queue_item.retry_count
                )
                
            return None
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to read message from queue: {e}")
            return None
        finally:
            db.close()
    
    @staticmethod
    def delete(queue_name: str, msg_id: str) -> bool:
        """Mark a message as processed (successful completion)"""
        db: Session = SessionLocal()
        try:
            queue_item = db.query(TaskQueue).filter(TaskQueue.id == msg_id).first()
            
            if queue_item:
                queue_item.processed = True
                queue_item.processed_at = get_now()
                db.commit()
                logger.info(f"Marked message as processed: {msg_id}")
                return True
            
            logger.warning(f"Message not found for deletion: {msg_id}")
            return False
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to delete message from queue: {e}")
            return False
        finally:
            db.close()
    
    @staticmethod
    def retry_message(queue_name: str, msg_id: str) -> bool:
        """Mark a message for retry (failed processing)"""
        db: Session = SessionLocal()
        try:
            queue_item = db.query(TaskQueue).filter(TaskQueue.id == msg_id).first()
            
            if queue_item:
                queue_item.retry_count += 1
                queue_item.processing_started_at = None
                
                if queue_item.retry_count >= queue_item.max_retries:
                    queue_item.processed = True
                    queue_item.processed_at = get_now()
                    logger.warning(f"Message exceeded max retries: {msg_id}")
                else:
                    logger.info(f"Message marked for retry: {msg_id} (attempt {queue_item.retry_count})")
                
                db.commit()
                return True
            
            logger.warning(f"Message not found for retry: {msg_id}")
            return False
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to retry message: {e}")
            return False
        finally:
            db.close()
    


class QueueMessage:
    """Message object compatible with pgmq Message interface"""
    
    def __init__(self, msg_id: str, message: Dict[str, Any], retry_count: int = 0):
        self.msg_id = msg_id
        self.message = message
        self.retry_count = retry_count
