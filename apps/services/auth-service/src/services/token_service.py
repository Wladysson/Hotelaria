from datetime import datetime
from uuid import UUID

from src.core.jwt import (
    JWTError,
    TokenType,
    create_access_token,
    create_email_verification_token,
    create_password_reset_token,
    create_refresh_token,
    decode_token,
    get_token_jti,
    get_token_subject,
    get_token_type,
)
from src.models.user import User
from src.schemas.token import (
    AccessTokenResponse,
    AuthenticationResponse,
)


class TokenService:

    def create_access_token(
        self,
        user: User,
    ) -> tuple[str, str, datetime]:
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

        return create_access_token(
            user.id,
            roles=roles,
            permissions=permissions,
        )

    def create_refresh_token(
        self,
        user: User,
    ) -> tuple[str, str, datetime]:
        return create_refresh_token(
            user.id
        )

    def create_authentication_tokens(
        self,
        user: User,
    ) -> AuthenticationResponse:
        access_token, _, access_expires_at = (
            self.create_access_token(user)
        )

        refresh_token, _, refresh_expires_at = (
            self.create_refresh_token(user)
        )

        now = datetime.now(
            access_expires_at.tzinfo
        )

        return AuthenticationResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=max(
                int(
                    (
                        access_expires_at - now
                    ).total_seconds()
                ),
                0,
            ),
            refresh_expires_in=max(
                int(
                    (
                        refresh_expires_at - now
                    ).total_seconds()
                ),
                0,
            ),
        )

    def create_password_reset_token(
        self,
        user: User,
    ) -> tuple[str, str, datetime]:
        return create_password_reset_token(
            user.id
        )

    def create_email_verification_token(
        self,
        user: User,
    ) -> tuple[str, str, datetime]:
        return create_email_verification_token(
            user.id
        )

    def validate_access_token(
        self,
        token: str,
    ) -> UUID:
        payload = self._decode_and_validate_type(
            token,
            TokenType.ACCESS,
        )

        return self._extract_subject(
            payload
        )

    def validate_refresh_token(
        self,
        token: str,
    ) -> UUID:
        payload = self._decode_and_validate_type(
            token,
            TokenType.REFRESH,
        )

        return self._extract_subject(
            payload
        )

    def validate_password_reset_token(
        self,
        token: str,
    ) -> UUID:
        payload = self._decode_and_validate_type(
            token,
            TokenType.PASSWORD_RESET,
        )

        return self._extract_subject(
            payload
        )

    def validate_email_verification_token(
        self,
        token: str,
    ) -> UUID:
        payload = self._decode_and_validate_type(
            token,
            TokenType.EMAIL_VERIFICATION,
        )

        return self._extract_subject(
            payload
        )

    def get_jti(
        self,
        token: str,
    ) -> str:
        try:
            return get_token_jti(token)
        except JWTError:
            raise

    def get_token_type(
        self,
        token: str,
    ) -> str:
        return get_token_type(token)

    def decode(
        self,
        token: str,
    ) -> dict:
        return decode_token(token)

    def _decode_and_validate_type(
        self,
        token: str,
        expected_type: str,
    ) -> dict:
        payload = decode_token(token)

        if payload.get("type") != expected_type:
            raise JWTError(
                f"Token do tipo {expected_type} obrigatório."
            )

        return payload

    @staticmethod
    def _extract_subject(
        payload: dict,
    ) -> UUID:
        try:
            return UUID(
                str(payload["sub"])
            )
        except (
            KeyError,
            TypeError,
            ValueError,
        ) as exc:
            raise JWTError(
                "Subject do token inválido."
            ) from exc