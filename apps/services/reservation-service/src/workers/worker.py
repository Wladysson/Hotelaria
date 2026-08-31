import asyncio
import logging

logger = logging.getLogger(__name__)


async def start_worker() -> None:

    logger.info("Reservation worker iniciado.")

    while True:
        await asyncio.sleep(60)


async def shutdown_worker() -> None:
    """
    Finaliza os recursos utilizados pelo worker.
    """

    logger.info("Reservation worker finalizado.")


async def main() -> None:
    """
    Ponto de entrada do processo worker.
    """

    try:
        await start_worker()
    except asyncio.CancelledError:
        logger.info("Worker recebeu sinal de cancelamento.")
        await shutdown_worker()
        raise


if __name__ == "__main__":
    asyncio.run(main())