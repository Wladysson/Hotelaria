from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.jwt import (
    TokenType,
    create_access_token,
    create_email_verification_token,
    create_password_reset_token,
    create_refresh_token,
    decode_token,
)
from src.core.security import (
    check_password,
    create_password_hash,
    validate_password_strength,
)
from src.models.user import User
from src.repositories.user_repository import UserRepository
from src.schemas.auth import (
    AuthenticationResponse,
    LoginRequest,
)


class AuthService:

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session
        self.user_repository = UserRepository(
            session
        )

    async def authenticate(
        self,
        credentials: LoginRequest,
    ) -> AuthenticationResponse:
        user = await self.user_repository.get_by_login(
            credentials.username
        )

        if user is None:
            raise self._invalid_credentials()

        self._validate_user_can_login(user)

        password_valid = check_password(
            credentials.password,
            user.password_hash,
        )

        if not password_valid:
            await self._handle_failed_login(user)

            raise self._invalid_credentials()

        await self.user_repository.update_last_login(
            user
        )

        return self._generate_authentication_response(
            user
        )

    async def refresh_access_token(
        self,
        refresh_token: str,
    ) -> AuthenticationResponse:
        payload = decode_token(refresh_token)

        if payload.get("type") != TokenType.REFRESH:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token inválido.",
                headers={
                    "WWW-Authenticate": "Bearer",
                },
            )

        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token inválido.",
                headers={
                    "WWW-Authenticate": "Bearer",
                },
            )

        try:
            parsed_user_id = UUID(str(user_id))
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token inválido.",
                headers={
                    "WWW-Authenticate": "Bearer",
                },
            ) from exc

        user = await self.user_repository.get_by_id_with_authorization(
            parsed_user_id
        )

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuário não encontrado.",
                headers={
                    "WWW-Authenticate": "Bearer",
                },
            )

        self._validate_user_can_login(user)

        return self._generate_authentication_response(
            user
        )

    async def create_password_reset_token(
        self,
        user: User,
    ) -> str:
        token, _, _ = create_password_reset_token(
            user.id
        )

        return token

    async def create_email_verification_token(
        self,
        user: User,
    ) -> str:
        token, _, _ = create_email_verification_token(
            user.id
        )

        return token

    async def reset_password(
        self,
        user: User,
        new_password: str,
    ) -> User:
        validate_password_strength(
            new_password
        )

        password_hash = create_password_hash(
            new_password
        )

        return await self.user_repository.update_password(
            user,
            password_hash,
        )

    async def change_password(
        self,
        user: User,
        current_password: str,
        new_password: str,
    ) -> User:
        if not check_password(
            current_password,
            user.password_hash,
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Senha atual inválida.",
            )

        if current_password == new_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A nova senha deve ser diferente da senha atual.",
            )

        validate_password_strength(
            new_password
        )

        password_hash = create_password_hash(
            new_password
        )

        return await self.user_repository.update_password(
            user,
            password_hash,
        )

    def _generate_authentication_response(
        self,
        user: User,
    ) -> AuthenticationResponse:
        roles = [
            role.name
            for role in user.roles
            if role.is_active
        ]

        permissions = sorted(
            {
                permission.name
                for role in user.roles
                if role.is_active
                for permission in role.permissions
                if permission.is_active
            }
        )

        access_token, _, _ = create_access_token(
            user.id,
            roles=roles,
            permissions=permissions,
        )

        refresh_token, _, _ = create_refresh_token(
            user.id
        )

        return AuthenticationResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=(
                settings.access_token_expire_minutes
                * 60
            ),
            refresh_expires_in=(
                settings.refresh_token_expire_days
                * 24
                * 60
                * 60
            ),
        )

    async def _handle_failed_login(
        self,
        user: User,
    ) -> None:
        await self.user_repository.increment_failed_login(
            user
        )

        if (
            user.failed_login_attempts
            >= settings.login_max_attempts
        ):
            locked_until = (
                datetime.now(timezone.utc)
                + timedelta(
                    minutes=settings.login_lockout_minutes
                )
            )

            await self.user_repository.lock_user(
                user,
                locked_until,
            )

    def _validate_user_can_login(
        self,
        user: User,
    ) -> None:
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuário inativo.",
            )

        if user.is_locked:
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Usuário temporariamente bloqueado.",
            )

    @staticmethod
    def _invalid_credentials() -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha inválidos.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )