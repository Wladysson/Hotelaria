from typing import Any


async def process_reservation_task(
    reservation_id: str,
    payload: dict[str, Any] | None = None,
) -> None:

    data = payload or {}

    # Processamento assíncrono da reserva.
    _ = reservation_id
    _ = data