from turtle import update
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from pydantic import BaseModel

from src.constants.enums import StopAt, TaskStatus
from src.db.connection import SessionLocal
from src.db.models import Task, Clip, Term, ClipTerm


class TaskCrud:
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
    def add_task(params: BaseModel, stop_at: StopAt) -> str:
        task = Task(stop_at=stop_at.value, params=params.model_dump())
        with SessionLocal() as session:
            session.add(task)
            session.commit()
            return str(task.id)

    @staticmethod
    def update_task(id: str, status: TaskStatus, result: dict = None, failed_reason: str = "") -> int:
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
    def delete_task(task_id: str):
        with SessionLocal() as session:
            task = session.query(Task).filter(Task.id == task_id).first()
            if task:
                session.delete(task)
                session.commit()
                return task
            return None

    @staticmethod
    def add_clip_with_terms(session: Session, clip_id: int, term_names: list[str]):
        existing_terms = session.query(Term).filter(Term.name.in_(term_names)).all()
        existing_term_map = {term.name: term.id for term in existing_terms}

        new_term_names = set(term_names) - existing_term_map.keys()
        new_terms = [Term(name=name) for name in new_term_names]

        if new_terms:
            session.add_all(new_terms)
            session.commit()

            inserted_terms = session.query(Term).filter(Term.name.in_(new_term_names)).all()
            for term in inserted_terms:
                existing_term_map[term.name] = term.id

        clip_term_entries = [
            {"clip_id": clip_id, "term_id": term_id}
            for term_id in existing_term_map.values()
        ]

        dialect = session.bind.dialect.name
        if dialect == "postgresql":
            stmt = pg_insert(ClipTerm).values(clip_term_entries).on_conflict_do_nothing()
            session.execute(stmt)

        elif dialect == "mysql":
            stmt = mysql_insert(ClipTerm).values(clip_term_entries).prefix_with("IGNORE")
            session.execute(stmt)
        else:
            for entry in clip_term_entries:
                try:
                    session.add(ClipTerm(**entry))
                    session.commit()
                except IntegrityError:
                    session.rollback()

        session.commit()
