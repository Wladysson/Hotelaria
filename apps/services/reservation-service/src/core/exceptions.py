from typing import Any


class ReservationServiceException(Exception):
    """
    Exceção base do Reservation Service.
    """

    status_code: int = 500
    error_code: str = "RESERVATION_SERVICE_ERROR"

    def __init__(
        self,
        message: str,
        *,
        details: Any | None = None,
    ) -> None:
        super().__init__(message)

        self.message = message
        self.details = details


class ResourceNotFoundException(ReservationServiceException):
    """
    Recurso solicitado não encontrado.
    """

    status_code = 404
    error_code = "RESOURCE_NOT_FOUND"


class ReservationNotFoundException(ResourceNotFoundException):
    """
    Reserva não encontrada.
    """

    error_code = "RESERVATION_NOT_FOUND"


class HoldNotFoundException(ResourceNotFoundException):
    """
    Hold não encontrado.
    """

    error_code = "HOLD_NOT_FOUND"


class GuestNotFoundException(ResourceNotFoundException):
    """
    Hóspede não encontrado.
    """

    error_code = "GUEST_NOT_FOUND"


class BusinessRuleException(ReservationServiceException):
    """
    Violação de uma regra de negócio.
    """

    status_code = 422
    error_code = "BUSINESS_RULE_VIOLATION"


class ReservationUnavailableException(BusinessRuleException):
    """
    Não existe disponibilidade para a reserva solicitada.
    """

    error_code = "RESERVATION_UNAVAILABLE"


class InvalidReservationStatusException(BusinessRuleException):
    """
    Operação incompatível com o status atual da reserva.
    """

    error_code = "INVALID_RESERVATION_STATUS"


class HoldExpiredException(BusinessRuleException):
    """
    Hold expirado.
    """

    error_code = "HOLD_EXPIRED"


class HoldAlreadyExistsException(BusinessRuleException):
    """
    Já existe um hold ativo para o recurso solicitado.
    """

    error_code = "HOLD_ALREADY_EXISTS"


class CancellationNotAllowedException(BusinessRuleException):
    """
    Cancelamento não permitido pelas regras da reserva.
    """

    error_code = "CANCELLATION_NOT_ALLOWED"


class InvalidDateRangeException(BusinessRuleException):
    """
    Intervalo de datas inválido.
    """

    error_code = "INVALID_DATE_RANGE"


class ConflictException(ReservationServiceException):
    """
    Conflito de estado ou concorrência.
    """

    status_code = 409
    error_code = "RESOURCE_CONFLICT"


class InventoryConflictException(ConflictException):
    """
    Conflito relacionado ao inventário de quartos.
    """

    error_code = "INVENTORY_CONFLICT"


class PersistenceException(ReservationServiceException):
    """
    Erro relacionado à persistência.
    """

    status_code = 500
    error_code = "PERSISTENCE_ERROR"


class ExternalServiceException(ReservationServiceException):
    """
    Falha na comunicação com serviço externo.
    """

    status_code = 502
    error_code = "EXTERNAL_SERVICE_ERROR"


class PaymentServiceException(ExternalServiceException):
    """
    Falha na comunicação com o serviço de pagamentos.
    """

    error_code = "PAYMENT_SERVICE_ERROR"


class NotificationServiceException(ExternalServiceException):
    """
    Falha na comunicação com o serviço de notificações.
    """

    error_code = "NOTIFICATION_SERVICE_ERROR"