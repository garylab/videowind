from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from src.constants.config import config


engine = create_engine(
    config.DB.url,
    pool_pre_ping=config.DB.pre_ping,
    pool_size=config.DB.pool_size,
    max_overflow=config.DB.max_overflow
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    Base.metadata.create_all(engine)