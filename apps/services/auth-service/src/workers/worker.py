import asyncio
import logging

from src.workers.tasks.cleanup import (
    cleanup_expired_sessions,
)
from src.workers.tasks.security import (
    process_security_tasks,
)


logger = logging.getLogger(
    "auth-service.worker"
)


async def run_worker() -> None:
    logger.info(
        "Auth worker started"
    )

    while True:
        try:
            await cleanup_expired_sessions()

            await process_security_tasks()

        except asyncio.CancelledError:
            logger.info(
                "Auth worker shutdown requested"
            )

            raise

        except Exception:
            logger.exception(
                "Unexpected error in auth worker"
            )

        await asyncio.sleep(
            60
        )


def main() -> None:
    try:
        asyncio.run(
            run_worker()
        )
    except KeyboardInterrupt:
        logger.info(
            "Auth worker stopped"
        )


if __name__ == "__main__":
    main()