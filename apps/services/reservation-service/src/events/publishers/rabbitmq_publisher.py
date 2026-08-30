from typing import Any

from src.events.publishers.event_publisher import EventPublisher


class RabbitMQEventPublisher(EventPublisher):

    def __init__(
        self,
        exchange: str,
    ) -> None:
        self.exchange = exchange

    async def publish(
        self,
        event_type: str,
        payload: dict[str, Any],
        routing_key: str,
    ) -> None:
        """
        Publica um evento no exchange configurado.
        """

        # Integração RabbitMQ será realizada na camada de infraestrutura.
        return None