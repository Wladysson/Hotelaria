from datetime import date
from decimal import Decimal
from uuid import UUID

from src.core.exceptions import ReservationConflictError


class PricingService:
    """
    Serviço responsável pelo cálculo financeiro das reservas.

    Centraliza:
    - preço das diárias;
    - quantidade de noites;
    - quantidade de quartos;
    - descontos;
    - taxas;
    - valor total da reserva.
    """

    def calculate_nights(
        self,
        check_in: date,
        check_out: date,
    ) -> int:
        if check_out <= check_in:
            raise ReservationConflictError(
                "A data de checkout deve ser posterior ao check-in."
            )

        return (check_out - check_in).days

    def calculate_room_subtotal(
        self,
        price_per_night: Decimal,
        check_in: date,
        check_out: date,
        rooms: int,
    ) -> Decimal:
        if price_per_night < 0:
            raise ReservationConflictError(
                "O preço da diária não pode ser negativo."
            )

        if rooms < 1:
            raise ReservationConflictError(
                "A quantidade de quartos deve ser maior que zero."
            )

        nights = self.calculate_nights(
            check_in=check_in,
            check_out=check_out,
        )

        return (
            price_per_night
            * Decimal(nights)
            * Decimal(rooms)
        )

    def calculate_discount(
        self,
        subtotal: Decimal,
        discount_percent: Decimal = Decimal("0"),
    ) -> Decimal:
        if subtotal < 0:
            raise ReservationConflictError(
                "O subtotal não pode ser negativo."
            )

        if discount_percent < 0 or discount_percent > 100:
            raise ReservationConflictError(
                "O percentual de desconto deve estar entre 0 e 100."
            )

        return (
            subtotal
            * discount_percent
            / Decimal("100")
        )

    def calculate_tax(
        self,
        amount: Decimal,
        tax_percent: Decimal = Decimal("0"),
    ) -> Decimal:
        if amount < 0:
            raise ReservationConflictError(
                "O valor para cálculo da taxa não pode ser negativo."
            )

        if tax_percent < 0 or tax_percent > 100:
            raise ReservationConflictError(
                "O percentual de taxa deve estar entre 0 e 100."
            )

        return (
            amount
            * tax_percent
            / Decimal("100")
        )

    def calculate_total(
        self,
        price_per_night: Decimal,
        check_in: date,
        check_out: date,
        rooms: int,
        discount_percent: Decimal = Decimal("0"),
        tax_percent: Decimal = Decimal("0"),
    ) -> Decimal:
        subtotal = self.calculate_room_subtotal(
            price_per_night=price_per_night,
            check_in=check_in,
            check_out=check_out,
            rooms=rooms,
        )

        discount = self.calculate_discount(
            subtotal=subtotal,
            discount_percent=discount_percent,
        )

        amount_after_discount = subtotal - discount

        tax = self.calculate_tax(
            amount=amount_after_discount,
            tax_percent=tax_percent,
        )

        return amount_after_discount + tax