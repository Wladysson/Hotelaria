class AuthServiceError(Exception):
    """Exceção base do Auth Service."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class InvalidCredentialsError(AuthServiceError):
    """Credenciais inválidas."""

    def __init__(
        self,
        message: str = "E-mail ou senha inválidos.",
    ) -> None:
        super().__init__(message)


class UserAlreadyExistsError(AuthServiceError):
    """Tentativa de cadastrar usuário existente."""

    def __init__(
        self,
        message: str = "Usuário já cadastrado.",
    ) -> None:
        super().__init__(message)


class UserNotFoundError(AuthServiceError):
    """Usuário não encontrado."""

    def __init__(
        self,
        message: str = "Usuário não encontrado.",
    ) -> None:
        super().__init__(message)


class InactiveUserError(AuthServiceError):
    """Usuário está inativo."""

    def __init__(
        self,
        message: str = "Usuário está inativo.",
    ) -> None:
        super().__init__(message)


class InvalidTokenError(AuthServiceError):
    """Token JWT inválido ou expirado."""

    def __init__(
        self,
        message: str = "Token inválido ou expirado.",
    ) -> None:
        super().__init__(message)


class ForbiddenError(AuthServiceError):
    """Usuário autenticado não possui permissão."""

    def __init__(
        self,
        message: str = "Você não possui permissão para executar esta operação.",
    ) -> None:
        super().__init__(message)