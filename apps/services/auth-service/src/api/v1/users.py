from uuid import UUID

from fastapi import APIRouter, Depends, status

from src.api.deps import get_current_user
from src.models.user import User
from src.schemas.user import UserResponse

router = APIRouter()


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
)
async def get_authenticated_user(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    return UserResponse.model_validate(current_user)