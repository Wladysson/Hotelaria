from fastapi import HTTPException, status

from src.core.jwt import (
    create_access_token,
    create_refresh_token,
    decode_token,
)
from src.schemas.token import TokenResponse


class TokenService:

    def create_tokens(
        self,
        user_id: str,
        email: str,
        roles: list[str],
    ) -> TokenResponse:
        claims = {
            "email": email,
            "roles": roles,
        }

        access_token = create_access_token(
            subject=user_id,
            claims=claims,
        )

        refresh_token = create_refresh_token(
            subject=user_id,
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=900,
        )

    def refresh_access_token(
        self,
        refresh_token: str,
    ) -> TokenResponse:
        try:
            payload = decode_token(refresh_token)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        subject = payload.get("sub")

        if not subject:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token subject",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token = create_access_token(
            subject=subject,
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=900,
        )