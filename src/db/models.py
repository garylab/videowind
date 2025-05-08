from sqlalchemy import Column, Integer, String, ForeignKey, Enum, Text, DateTime, JSON, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from uuid6 import uuid7
from src.constants.enums import TaskStatus
from src.db.connection import Base
from src.utils.date_utils import get_now


class BaseModel(Base):
    __abstract__ = True

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid7, unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_now)
    updated_at = Column(DateTime(timezone=True), default=get_now, onupdate=get_now)


class Task(BaseModel):
    __tablename__ = "tasks"

    status = Column(String(30), default=TaskStatus.INIT.value)
    stop_at = Column(String(30), nullable=False, default="")
    params = Column(JSON, default={})
    result = Column(JSON, default={})
    failed_reason = Column(Text, default="")


class Clip(BaseModel):
    __tablename__ = "clips"

    provider = Column(String(30), nullable=False, default="")
    original_id = Column(String(50), nullable=False, default="")

    path = Column(String(255), nullable=False, unique=True, default="")
    url = Column(String(255), nullable=False, default="")
    thumbnail = Column(String(255), nullable=False, default="")
    width = Column(Integer, nullable=False, default=0)
    height = Column(Integer, nullable=False, default=0)
    duration = Column(Integer, nullable=False, default=0)
    description = Column(Text, default="")

    __table_args__ = (UniqueConstraint("provider", "original_id"),)


class Term(BaseModel):
    __tablename__ = "terms"

    name = Column(String(50), nullable=False, unique=True)


class ClipTerm(BaseModel):
    __tablename__ = "clips_terms"

    clip_id = Column(UUID(as_uuid=True), ForeignKey("clips.id"),  nullable=False)
    term_id = Column(UUID(as_uuid=True), ForeignKey("terms.id"), nullable=False)

    __table_args__ = (UniqueConstraint("clip_id", "term_id"),)


class WordpressWebsite(BaseModel):
    __tablename__ = "wordpress_websites"

    url = Column(String(255), nullable=False, unique=True)
    username = Column(String(50), nullable=False, default="")
    password = Column(String(50), nullable=False, default="")


class WordpressPost(BaseModel):
    __tablename__ = "wordpress_posts"

    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False)
    post_id = Column(UUID(as_uuid=True), nullable=False, unique=True)

    status = Column(Integer, default=TaskStatus.INIT.value)

