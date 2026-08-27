from uuid import UUID

from fastapi import APIRouter, Depends, status

from src.api.deps import (
    CurrentUser,
    UserServiceDependency,
    require_permissions,
    require_superuser,
)
from src.schemas.user import (
    UserAdminUpdate,
    UserCreate,
    UserResponse,
    UserRoleAssignment,
    UserSummary,
    UserUpdate,
)


router = APIRouter()


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cria um novo usuário",
)
async def create_user(
    data: UserCreate,
    user_service: UserServiceDependency,
) -> UserResponse:
    user = await user_service.create_user(data)

    await user_service.session.commit()

    return user


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtém os dados do próprio usuário",
)
async def get_me(
    current_user: CurrentUser,
) -> UserResponse:
    return current_user


@router.put(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Atualiza os próprios dados",
)
async def update_me(
    data: UserUpdate,
    current_user: CurrentUser,
    user_service: UserServiceDependency,
) -> UserResponse:
    user = await user_service.update_user(
        current_user,
        data,
    )

    await user_service.session.commit()

    return user


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtém um usuário",
    dependencies=[
        Depends(
            require_permissions("users:read")
        )
    ],
)
async def get_user(
    user_id: UUID,
    user_service: UserServiceDependency,
) -> UserResponse:
    return await user_service.get_user(
        user_id
    )


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Atualiza um usuário",
    dependencies=[
        Depends(
            require_permissions("users:update")
        )
    ],
)
async def update_user(
    user_id: UUID,
    data: UserAdminUpdate,
    user_service: UserServiceDependency,
) -> UserResponse:
    user = await user_service.get_user(
        user_id
    )

    user = await user_service.admin_update_user(
        user,
        data,
    )

    await user_service.session.commit()

    return user


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove um usuário",
    dependencies=[
        Depends(
            require_permissions("users:delete")
        )
    ],
)
async def delete_user(
    user_id: UUID,
    user_service: UserServiceDependency,
) -> None:
    user = await user_service.get_user(
        user_id
    )

    await user_service.delete_user(user)

    await user_service.session.commit()


@router.put(
    "/{user_id}/roles",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Atribui roles ao usuário",
    dependencies=[
        Depends(
            require_permissions("users:update")
        )
    ],
)
async def assign_roles(
    user_id: UUID,
    data: UserRoleAssignment,
    user_service: UserServiceDependency,
) -> UserResponse:
    user = await user_service.get_user(
        user_id
    )

    user = await user_service.assign_roles(
        user,
        data,
    )

    await user_service.session.commit()

    return user


@router.delete(
    "/{user_id}/roles",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Remove todas as roles do usuário",
    dependencies=[
        Depends(
            require_permissions("users:update")
        )
    ],
)
async def remove_roles(
    user_id: UUID,
    user_service: UserServiceDependency,
) -> UserResponse:
    user = await user_service.get_user(
        user_id
    )

    user = await user_service.remove_all_roles(
        user
    )

    await user_service.session.commit()

    return user


@router.patch(
    "/{user_id}/activate",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Ativa um usuário",
    dependencies=[
        Depends(
            require_permissions("users:update")
        )
    ],
)
async def activate_user(
    user_id: UUID,
    user_service: UserServiceDependency,
) -> UserResponse:
    user = await user_service.get_user(
        user_id
    )

    user = await user_service.activate_user(
        user
    )

    await user_service.session.commit()

    return user


@router.patch(
    "/{user_id}/deactivate",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Desativa um usuário",
    dependencies=[
        Depends(
            require_permissions("users:update")
        )
    ],
)
async def deactivate_user(
    user_id: UUID,
    user_service: UserServiceDependency,
) -> UserResponse:
    user = await user_service.get_user(
        user_id
    )

    user = await user_service.deactivate_user(
        user
    )

    await user_service.session.commit()

    return user