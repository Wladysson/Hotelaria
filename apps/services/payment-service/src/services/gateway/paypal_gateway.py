from base64 import b64encode
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


class PayPalGateway(PaymentGateway):
    @property
    def provider_name(self) -> str:
        return "paypal"

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

        access_token = await self._get_access_token()

        payload = {
            "intent": "CAPTURE",
            "purchase_units": [
                {
                    "reference_id": transaction_id,
                    "amount": {
                        "currency_code": currency.upper(),
                        "value": str(amount),
                    },
                    "description": description,
                }
            ],
            "application_context": {
                "user_action": "PAY_NOW",
            },
        }

        response = await self._request(
            method="POST",
            endpoint="/v2/checkout/orders",
            access_token=access_token,
            json=payload,
        )

        status = response.get("status", "").lower()

        if status in {"declined", "failed"}:
            raise PaymentGatewayDeclinedError(
                "O PayPal recusou o pagamento."
            )

        return {
            "id": response.get("id"),
            "gateway_transaction_id": response.get("id"),
            "status": (
                "succeeded"
                if status == "completed"
                else "processing"
            ),
            "captured_amount": (
                amount if status == "completed" else Decimal("0.00")
            ),
            "raw_response": response,
        }

    async def capture_payment(
        self,
        *,
        gateway_transaction_id: str,
        amount: Decimal | None = None,
    ) -> dict[str, Any]:

        access_token = await self._get_access_token()

        response = await self._request(
            method="POST",
            endpoint=(
                f"/v2/checkout/orders/"
                f"{gateway_transaction_id}/capture"
            ),
            access_token=access_token,
            json={},
        )

        status = response.get("status", "").lower()

        if status != "completed":
            raise PaymentGatewayError(
                "O PayPal não concluiu a captura."
            )

        captured_amount = self._extract_captured_amount(
            response
        )

        if captured_amount == Decimal("0.00") and amount is not None:
            captured_amount = amount

        return {
            "id": response.get("id"),
            "gateway_transaction_id": gateway_transaction_id,
            "status": "succeeded",
            "captured_amount": captured_amount,
            "raw_response": response,
        }

    async def cancel_payment(
        self,
        *,
        gateway_transaction_id: str,
    ) -> dict[str, Any]:

        raise PaymentGatewayError(
            "Cancelamento de pedidos PayPal deve ser tratado "
            "pela operação específica do pedido/captura."
        )

    async def refund_payment(
        self,
        *,
        gateway_transaction_id: str,
        amount: Decimal | None = None,
        reason: str | None = None,
    ) -> dict[str, Any]:

        access_token = await self._get_access_token()

        payload = {}

        if amount is not None:
            payload["amount"] = {
                "value": str(amount),
                "currency_code": "BRL",
            }

        if reason:
            payload["note_to_payer"] = reason

        response = await self._request(
            method="POST",
            endpoint=(
                f"/v2/payments/captures/"
                f"{gateway_transaction_id}/refund"
            ),
            access_token=access_token,
            json=payload,
        )

        status = response.get("status", "").lower()

        return {
            "id": response.get("id"),
            "gateway_refund_id": response.get("id"),
            "status": (
                "succeeded"
                if status == "completed"
                else "processing"
            ),
            "raw_response": response,
        }

    async def get_payment(
        self,
        *,
        gateway_transaction_id: str,
    ) -> dict[str, Any]:

        access_token = await self._get_access_token()

        response = await self._request(
            method="GET",
            endpoint=(
                f"/v2/checkout/orders/"
                f"{gateway_transaction_id}"
            ),
            access_token=access_token,
        )

        return {
            "id": response.get("id"),
            "gateway_transaction_id": response.get("id"),
            "status": response.get("status"),
            "raw_response": response,
        }

    async def _get_access_token(self) -> str:
        if not settings.PAYPAL_CLIENT_ID:
            raise PaymentGatewayError(
                "PAYPAL_CLIENT_ID não configurado."
            )

        if not settings.PAYPAL_CLIENT_SECRET:
            raise PaymentGatewayError(
                "PAYPAL_CLIENT_SECRET não configurado."
            )

        credentials = (
            f"{settings.PAYPAL_CLIENT_ID}:"
            f"{settings.PAYPAL_CLIENT_SECRET}"
        )

        encoded_credentials = b64encode(
            credentials.encode()
        ).decode()

        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        try:
            async with httpx.AsyncClient(
                timeout=settings.PAYMENT_TIMEOUT_SECONDS,
            ) as client:
                response = await client.post(
                    f"{settings.PAYPAL_BASE_URL}/v1/oauth2/token",
                    headers=headers,
                    data={
                        "grant_type": "client_credentials",
                    },
                )

        except httpx.TimeoutException as exc:
            raise PaymentGatewayTimeoutError(
                "Timeout ao autenticar no PayPal."
            ) from exc

        except httpx.HTTPError as exc:
            raise PaymentGatewayError(
                "Erro de comunicação com a autenticação do PayPal."
            ) from exc

        if response.status_code >= 400:
            raise PaymentGatewayError(
                "Falha ao obter token de acesso do PayPal."
            )

        body = response.json()
        access_token = body.get("access_token")

        if not access_token:
            raise PaymentGatewayError(
                "O PayPal não retornou um token de acesso válido."
            )

        return access_token

    async def _request(
        self,
        *,
        method: str,
        endpoint: str,
        access_token: str,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        try:
            async with httpx.AsyncClient(
                timeout=settings.PAYMENT_TIMEOUT_SECONDS,
            ) as client:
                response = await client.request(
                    method=method,
                    url=f"{settings.PAYPAL_BASE_URL}{endpoint}",
                    headers=headers,
                    json=json,
                )

        except httpx.TimeoutException as exc:
            raise PaymentGatewayTimeoutError(
                "Timeout na comunicação com o PayPal."
            ) from exc

        except httpx.HTTPError as exc:
            raise PaymentGatewayError(
                "Erro de comunicação com o PayPal."
            ) from exc

        if response.status_code in {400, 422}:
            raise PaymentGatewayDeclinedError(
                self._extract_error(response)
            )

        if response.status_code >= 400:
            raise PaymentGatewayError(
                self._extract_error(response)
            )

        if not response.content:
            return {}

        return response.json()

    @staticmethod
    def _extract_captured_amount(
        response: dict[str, Any],
    ) -> Decimal:

        total = Decimal("0.00")

        for purchase_unit in response.get(
            "purchase_units",
            [],
        ):
            payments = purchase_unit.get(
                "payments",
                {},
            )

            captures = payments.get(
                "captures",
                [],
            )

            for capture in captures:
                amount = capture.get(
                    "amount",
                    {},
                ).get(
                    "value",
                    "0.00",
                )

                total += Decimal(str(amount))

        return total

    @staticmethod
    def _extract_error(response: httpx.Response) -> str:
        try:
            body = response.json()

            return (
                body.get("message")
                or body.get("name")
                or "Erro retornado pelo PayPal."
            )

        except ValueError:
            return "Erro retornado pelo PayPal."