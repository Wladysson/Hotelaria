from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_db
from src.schemas.auth import LoginRequest
from src.schemas.token import TokenResponse
from src.services.auth_service import AuthService
from src.services.token_service import TokenService

router = APIRouter()


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
)
async def login(
    request: LoginRequest,
    session: AsyncSession = Depends(get_db),
):
    auth_service = AuthService(session)
    token_service = TokenService()

    user = await auth_service.authenticate(
        email=request.email,
        password=request.password,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    roles = [role.name for role in user.roles]

    return token_service.create_tokens(
        user_id=str(user.id),
        email=user.email,
        roles=roles,
    )