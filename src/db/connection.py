from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
# from pgmq_sqlalchemy import PGMQueue
from tembo_pgmq_python import PGMQueue, Message

from src.constants.config import DbConfig, env
from src.constants.consts import TASK_QUEUE_NAME

engine = create_engine(
    env.DB.url,
    pool_pre_ping=env.DB.pre_ping,
    pool_size=env.DB.pool_size,
    max_overflow=env.DB.max_overflow
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

pgmq = PGMQueue(host=engine.url.host,
                username=engine.url.username,
                password=engine.url.password,
                port=str(engine.url.port),
                database=engine.url.database)


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


def init_pgmq():
    pgmq.create_queue(TASK_QUEUE_NAME)


def create_tables():
    Base.metadata.create_all(engine)