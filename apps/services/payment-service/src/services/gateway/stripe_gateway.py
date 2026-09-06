from decimal import Decimal
from typing import Any

import httpx

from src.core.config import settings
from src.core.payment_gateway import (
    PaymentGateway,
    PaymentGatewayDeclinedError,
    PaymentGatewayError,
    PaymentGatewayTimeoutError,
)


class StripeGateway(PaymentGateway):
    BASE_URL = "https://api.stripe.com/v1"

    @property
    def provider_name(self) -> str:
        return "stripe"

    async def create_payment(
        self,
        *,
        transaction_id: str,
        amount: Decimal,
        currency: str,
        payment_method: str,
        description: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:

        if not settings.STRIPE_SECRET_KEY:
            raise PaymentGatewayError(
                "STRIPE_SECRET_KEY não configurada."
            )

        payload = {
            "amount": self._to_minor_units(amount),
            "currency": currency.lower(),
            "payment_method": payment_method,
            "confirm": "true",
        }

        if description:
            payload["description"] = description

        if metadata:
            for key, value in metadata.items():
                payload[f"metadata[{key}]"] = str(value)

        payload["metadata[transaction_id]"] = transaction_id

        response = await self._request(
            method="POST",
            endpoint="/payment_intents",
            data=payload,
        )

        status = response.get("status")

        if status == "requires_capture":
            normalized_status = "authorized"
        elif status == "succeeded":
            normalized_status = "succeeded"
        elif status in {
            "canceled",
            "payment_failed",
        }:
            raise PaymentGatewayDeclinedError(
                "O Stripe recusou o pagamento."
            )
        else:
            normalized_status = "processing"

        return {
            "id": response.get("id"),
            "gateway_transaction_id": response.get("id"),
            "status": normalized_status,
            "captured_amount": self._from_minor_units(
                response.get("amount_received", 0)
            ),
            "raw_response": response,
        }

    async def capture_payment(
        self,
        *,
        gateway_transaction_id: str,
        amount: Decimal | None = None,
    ) -> dict[str, Any]:

        payload = {}

        if amount is not None:
            payload["amount_to_capture"] = self._to_minor_units(amount)

        response = await self._request(
            method="POST",
            endpoint=f"/payment_intents/{gateway_transaction_id}/capture",
            data=payload,
        )

        return {
            "id": response.get("id"),
            "gateway_transaction_id": response.get("id"),
            "status": "succeeded",
            "captured_amount": self._from_minor_units(
                response.get("amount_received", 0)
            ),
            "raw_response": response,
        }

    async def cancel_payment(
        self,
        *,
        gateway_transaction_id: str,
    ) -> dict[str, Any]:

        response = await self._request(
            method="POST",
            endpoint=f"/payment_intents/{gateway_transaction_id}/cancel",
            data={},
        )

        return {
            "id": response.get("id"),
            "gateway_transaction_id": response.get("id"),
            "status": "cancelled",
            "raw_response": response,
        }

    async def refund_payment(
        self,
        *,
        gateway_transaction_id: str,
        amount: Decimal | None = None,
        reason: str | None = None,
    ) -> dict[str, Any]:

        payload = {
            "payment_intent": gateway_transaction_id,
        }

        if amount is not None:
            payload["amount"] = self._to_minor_units(amount)

        if reason:
            payload["metadata[reason]"] = reason

        response = await self._request(
            method="POST",
            endpoint="/refunds",
            data=payload,
        )

        status = response.get("status")

        return {
            "id": response.get("id"),
            "gateway_refund_id": response.get("id"),
            "status": (
                "succeeded"
                if status == "succeeded"
                else "processing"
            ),
            "raw_response": response,
        }

    async def get_payment(
        self,
        *,
        gateway_transaction_id: str,
    ) -> dict[str, Any]:

        response = await self._request(
            method="GET",
            endpoint=f"/payment_intents/{gateway_transaction_id}",
        )

        return {
            "id": response.get("id"),
            "gateway_transaction_id": response.get("id"),
            "status": response.get("status"),
            "captured_amount": self._from_minor_units(
                response.get("amount_received", 0)
            ),
            "raw_response": response,
        }

    async def _request(
        self,
        *,
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:

        headers = {
            "Authorization": f"Bearer {settings.STRIPE_SECRET_KEY}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        try:
            async with httpx.AsyncClient(
                timeout=settings.PAYMENT_TIMEOUT_SECONDS,
            ) as client:
                response = await client.request(
                    method=method,
                    url=f"{self.BASE_URL}{endpoint}",
                    headers=headers,
                    data=data,
                )

        except httpx.TimeoutException as exc:
            raise PaymentGatewayTimeoutError(
                "Timeout na comunicação com o Stripe."
            ) from exc

        except httpx.HTTPError as exc:
            raise PaymentGatewayError(
                "Erro de comunicação com o Stripe."
            ) from exc

        if response.status_code in {402, 409}:
            raise PaymentGatewayDeclinedError(
                self._extract_error(response)
            )

        if response.status_code >= 400:
            raise PaymentGatewayError(
                self._extract_error(response)
            )

        return response.json()

    @staticmethod
    def _to_minor_units(amount: Decimal) -> int:
        return int(amount * 100)

    @staticmethod
    def _from_minor_units(amount: int) -> Decimal:
        return Decimal(amount) / Decimal("100")

    @staticmethod
    def _extract_error(response: httpx.Response) -> str:
        try:
            body = response.json()
            return body.get("error", {}).get(
                "message",
                "Erro retornado pelo Stripe.",
            )
        except ValueError:
            return "Erro retornado pelo Stripe."