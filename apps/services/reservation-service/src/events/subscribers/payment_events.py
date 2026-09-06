from typing import Any


async def handle_payment_confirmed(
    payload: dict[str, Any],
) -> None:
    """
    Processa confirmação de pagamento.
    """

    # Atualizar reserva após confirmação do pagamento.
    return None


async def handle_payment_failed(
    payload: dict[str, Any],
) -> None:
    """
    Processa falha no pagamento.
    """

    # Cancelar ou liberar recursos da reserva.
    return None