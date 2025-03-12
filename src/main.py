import uvicorn
from loguru import logger

from src.constants.config import config


if __name__ == "__main__":
    logger.info(
        "start server, docs: http://127.0.0.1:" + str(config.APP.port) + "/docs"
    )
    uvicorn.run(
        app="src.asgi:app",
        host=config.APP.host,
        port=config.APP.port,
        reload=config.APP.reload,
        log_level="warning",
    )
