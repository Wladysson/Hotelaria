from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.jwt import create_access_token, create_refresh_token
from src.core.security import verify_password
from src.repositories.user_repository import UserRepository
from src.schemas.auth import LoginRequest
from src.schemas.token import TokenResponse


class AuthService:

    def __init__(self, session: AsyncSession) -> None:
        self.user_repository = UserRepository(session)

    async def authenticate(self, data: LoginRequest) -> TokenResponse:
        user = await self.user_repository.get_by_email(data.email)

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive",
            )

        if not verify_password(data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user.last_login_at = datetime.now(timezone.utc)

        await self.user_repository.update(user)

        roles = [role.name for role in user.roles]

        claims = {
            "email": user.email,
            "roles": roles,
        }

        access_token = create_access_token(
            subject=str(user.id),
            claims=claims,
        )

        refresh_token = create_refresh_token(
            subject=str(user.id),
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=900,
        )