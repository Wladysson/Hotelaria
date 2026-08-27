import asyncio
import logging
import signal
from collections.abc import Awaitable, Callable

logger = logging.getLogger("hotel-service.worker")


TaskHandler = Callable[[], Awaitable[None]]


class Worker:
    """
    Worker assíncrono responsável pela execução de tarefas
    em segundo plano do Hotel Service.
    """

    def __init__(
        self,
        interval_seconds: float = 5.0,
    ) -> None:
        self.interval_seconds = interval_seconds
        self._running = False
        self._stop_event = asyncio.Event()
        self._tasks: list[TaskHandler] = []

    def register_task(
        self,
        task: TaskHandler,
    ) -> None:
        """
        Registra uma tarefa para execução pelo worker.
        """
        if task not in self._tasks:
            self._tasks.append(task)

            logger.info(
                "Task registrada: %s",
                task.__name__,
            )

    async def start(self) -> None:
        """
        Inicia o worker.
        """
        if self._running:
            logger.warning(
                "Worker já está em execução."
            )
            return

        self._running = True
        self._stop_event.clear()

        logger.info(
            "Hotel Service Worker iniciado."
        )

        try:
            while self._running:
                await self._execute_tasks()

                try:
                    await asyncio.wait_for(
                        self._stop_event.wait(),
                        timeout=self.interval_seconds,
                    )
                except asyncio.TimeoutError:
                    continue

        finally:
            self._running = False

            logger.info(
                "Hotel Service Worker finalizado."
            )

    async def _execute_tasks(self) -> None:
        """
        Executa as tarefas registradas.
        """
        if not self._tasks:
            return

        results = await asyncio.gather(
            *(
                self._execute_task(task)
                for task in self._tasks
            ),
            return_exceptions=True,
        )

        for task, result in zip(
            self._tasks,
            results,
        ):
            if isinstance(result, Exception):
                logger.error(
                    "Erro na task %s: %s",
                    task.__name__,
                    result,
                    exc_info=result,
                )

    async def _execute_task(
        self,
        task: TaskHandler,
    ) -> None:
        """
        Executa uma task individual.
        """
        logger.debug(
            "Executando task: %s",
            task.__name__,
        )

        await task()

    async def stop(self) -> None:
        """
        Solicita a parada do worker.
        """
        if not self._running:
            return

        logger.info(
            "Solicitando parada do Hotel Service Worker."
        )

        self._running = False
        self._stop_event.set()


async def run_worker() -> None:
    """
    Inicializa e executa o worker principal.
    """
    worker = Worker()

    loop = asyncio.get_running_loop()

    def handle_shutdown() -> None:
        asyncio.create_task(
            worker.stop()
        )

    for signal_name in (
        signal.SIGINT,
        signal.SIGTERM,
    ):
        try:
            loop.add_signal_handler(
                signal_name,
                handle_shutdown,
            )
        except NotImplementedError:
            pass

    await worker.start()


def main() -> None:
    """
    Ponto de entrada do processo do worker.
    """
    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s | "
            "%(levelname)s | "
            "%(name)s | "
            "%(message)s"
        ),
    )

    try:
        asyncio.run(run_worker())
    except KeyboardInterrupt:
        logger.info(
            "Worker interrompido manualmente."
        )


if __name__ == "__main__":
    main()