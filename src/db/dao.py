from turtle import update

from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate

from src.constants.enums import StopAt, TaskStatus
from src.db.connection import SessionLocal
from src.db.models import Task


class Dao:
    @staticmethod
    def get_task(task_id: int):
        with SessionLocal() as session:
            return session.query(Task).filter(Task.id == task_id).first()

    @staticmethod
    def get_all_tasks(params: Params) -> Page[Task]:
        with SessionLocal() as session:
            query = session.query(Task)
            return paginate(session, query, params)

    @staticmethod
    def add_task(stop_at: StopAt, params: dict) -> int:
        task = Task(stop_at=stop_at.value, params=params)
        with SessionLocal() as session:
            session.add(task)
            session.commit()
            return task.id

    @staticmethod
    def update_task(id: int, status: TaskStatus, result: dict = None, failed_reason: str = "") -> int:
        with SessionLocal() as session:
            task = session.query(Task).filter(Task.id == id).first()
            if task:
                task.status = status.value
                if result:
                    task.result = result
                if failed_reason:
                    task.failed_reason = failed_reason
                session.commit()

            return task.id

    @staticmethod
    def delete_task(task_id: int):
        with SessionLocal() as session:
            task = session.query(Task).filter(Task.id == task_id).first()
            if task:
                session.delete(task)
                session.commit()
                return task
            return None