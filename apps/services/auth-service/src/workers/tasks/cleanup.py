import logging


logger = logging.getLogger(
    "auth-service.worker.cleanup"
)


async def cleanup_expired_sessions() -> None:
    logger.info(
        "Starting expired session cleanup"
    )

    # Session repository será conectado
    # quando a persistência de refresh tokens
    # for implementada.

    logger.info(
        "Expired session cleanup finished"
    )