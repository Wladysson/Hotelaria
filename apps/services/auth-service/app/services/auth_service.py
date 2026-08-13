from app.core.exceptions import (
    InactiveUserError,
    InvalidCredentialsError,
)
from app.core.security import (
    create_access_token,
    verify_password,
)
from app.repositories.usuario_repository import UsuarioRepository
from app.schemas.auth import LoginRequest, TokenResponse


class AuthService:
    def __init__(
        self,
        usuario_repository: UsuarioRepository,
    ) -> None:
        self.usuario_repository = usuario_repository

    async def login(
        self,
        data: LoginRequest,
    ) -> TokenResponse:
        usuario = await self.usuario_repository.get_by_email(
            data.email
        )

        if usuario is None:
            raise InvalidCredentialsError()

        if not usuario.is_active:
            raise InactiveUserError()

        password_valid = verify_password(
            data.password,
            usuario.password_hash,
        )

        if not password_valid:
            raise InvalidCredentialsError()

        access_token = create_access_token(
            subject=str(usuario.id),
            is_admin=usuario.is_admin,
        )

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
        )