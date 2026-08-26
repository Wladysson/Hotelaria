import logging


logger = logging.getLogger(
    "auth-service.worker.security"
)


async def process_security_tasks() -> None:
    logger.info(
        "Starting security background tasks"
    )

    logger.info(
        "Security background tasks finished"
    )