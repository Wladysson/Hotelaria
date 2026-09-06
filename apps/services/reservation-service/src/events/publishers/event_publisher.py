from abc import ABC, abstractmethod
from typing import Any


class EventPublisher(ABC):
    """
    Contrato para publicação de eventos de domínio.
    """

    @abstractmethod
    async def publish(
        self,
        event_type: str,
        payload: dict[str, Any],
        routing_key: str,
    ) -> None:
        """
        Publica um evento de domínio.
        """

        raise NotImplementedError