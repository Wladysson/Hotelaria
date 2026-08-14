import asyncio
import logging
import signal
from collections.abc import Coroutine
from typing import Any

from src.core.config import settings


logger = logging.getLogger(__name__)


class PaymentWorker:
    """
    Ponto de entrada do processamento assíncrono do payment-service.

    O worker centraliza o ciclo de vida do processo responsável
    por executar tarefas financeiras fora do ciclo HTTP.
    """

    def __init__(self) -> None:
        self._shutdown_event = asyncio.Event()
        self._tasks: set[asyncio.Task[Any]] = set()

    async def start(self) -> None:
        logger.info(
            "Iniciando payment worker | environment=%s",
            settings.ENVIRONMENT,
        )

        self._register_signal_handlers()

        await self._startup()

        try:
            await self._shutdown_event.wait()
        finally:
            await self.stop()

    async def stop(self) -> None:
        if self._shutdown_event.is_set():
            logger.info("Encerrando payment worker.")

        await self._cancel_tasks()
        await self._shutdown()

        logger.info("Payment worker encerrado.")

    async def _startup(self) -> None:
        """
        Inicializa os componentes necessários para processamento
        assíncrono.

        A conexão com RabbitMQ e o registro das tarefas serão
        adicionados conforme os consumers e tasks forem implementados.
        """

        logger.info("Componentes do worker inicializados.")

    async def _shutdown(self) -> None:
        """
        Libera recursos utilizados pelo processo do worker.
        """

        logger.info("Recursos do worker liberados.")

    async def _cancel_tasks(self) -> None:
        if not self._tasks:
            return

        logger.info(
            "Cancelando %d tarefa(s) em execução.",
            len(self._tasks),
        )

        for task in self._tasks:
            if not task.done():
                task.cancel()

        results = await asyncio.gather(
            *self._tasks,
            return_exceptions=True,
        )

        for result in results:
            if isinstance(result, Exception):
                logger.warning(
                    "Tarefa encerrada com erro: %s",
                    result,
                )

        self._tasks.clear()

    def create_task(
        self,
        coroutine: Coroutine[Any, Any, Any],
    ) -> asyncio.Task[Any]:
        """
        Registra uma tarefa assíncrona no ciclo de vida do worker.
        """

        task = asyncio.create_task(coroutine)
        self._tasks.add(task)

        task.add_done_callback(self._tasks.discard)

        return task

    def request_shutdown(self) -> None:
        """
        Solicita encerramento controlado do worker.
        """

        logger.info("Solicitação de encerramento recebida.")

        self._shutdown_event.set()

    def _register_signal_handlers(self) -> None:
        """
        Registra sinais de encerramento suportados pelo processo.
        """

        loop = asyncio.get_running_loop()

        for signal_name in (
            signal.SIGINT,
            signal.SIGTERM,
        ):
            try:
                loop.add_signal_handler(
                    signal_name,
                    self.request_shutdown,
                )
            except NotImplementedError:
                logger.warning(
                    "Signal handler não suportado para %s.",
                    signal_name,
                )


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s | %(levelname)s | "
            "%(name)s | %(message)s"
        ),
    )

    worker = PaymentWorker()
    await worker.start()


if __name__ == "__main__":
    asyncio.run(main())