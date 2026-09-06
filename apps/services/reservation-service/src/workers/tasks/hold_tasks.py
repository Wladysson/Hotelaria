from typing import Any


async def expire_hold_task(
    hold_id: str,
    payload: dict[str, Any] | None = None,
) -> None:

    data = payload or {}

    # Liberação assíncrona do hold expirado.
    _ = hold_id
    _ = data