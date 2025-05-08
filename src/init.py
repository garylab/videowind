import asyncio
from loguru import logger
from src.db.connection import create_tables, init_pgmq


async def init():
    create_tables()
    logger.info(f"Database tables created.")

    init_pgmq()
    logger.info(f"Message queue enabled and created.")


if __name__ == '__main__':
    asyncio.run(init())
