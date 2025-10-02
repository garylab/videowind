from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from src.constants.config import env

engine = create_engine(
    env.DB.url,
    pool_pre_ping=env.DB.pre_ping,
    pool_size=env.DB.pool_size,
    max_overflow=env.DB.max_overflow
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def create_tables():
    Base.metadata.create_all(engine)