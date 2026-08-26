from fastapi import APIRouter, Depends, status

from src.api.deps import get_current_user
from src.models.user import User
from src.schemas.user import RoleResponse

router = APIRouter()


@router.get(
    "/me",
    response_model=list[RoleResponse],
    status_code=status.HTTP_200_OK,
)
async def get_authenticated_user_roles(
    current_user: User = Depends(get_current_user),
) -> list[RoleResponse]:
    return [
        RoleResponse.model_validate(role)
        for role in current_user.roles
    ]