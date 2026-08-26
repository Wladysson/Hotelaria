from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.api.deps import require_permissions
from src.repositories.role_repository import RoleRepository
from src.api.deps import DBSession
from src.models.role import Role


router = APIRouter()


class RoleCreateRequest(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=100,
    )

    description: str | None = Field(
        default=None,
        max_length=255,
    )


class RoleUpdateRequest(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    description: str | None = Field(
        default=None,
        max_length=255,
    )

    is_active: bool | None = None


class RoleResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    is_active: bool


class PermissionResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    resource: str
    action: str
    is_active: bool


class RolePermissionsRequest(BaseModel):
    permission_ids: list[UUID] = Field(
        default_factory=list
    )


@router.post(
    "/",
    response_model=RoleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cria uma role",
    dependencies=[
        Depends(
            require_permissions("roles:create")
        )
    ],
)
async def create_role(
    data: RoleCreateRequest,
    db: DBSession,
) -> RoleResponse:
    repository = RoleRepository(db)

    name = data.name.strip().lower()

    if await repository.exists_by_name(name):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Role já cadastrada.",
        )

    role = Role(
        name=name,
        description=data.description,
        is_active=True,
    )

    role = await repository.create(role)

    await db.commit()

    return role


@router.get(
    "/",
    response_model=list[RoleResponse],
    status_code=status.HTTP_200_OK,
    summary="Lista as roles",
    dependencies=[
        Depends(
            require_permissions("roles:read")
        )
    ],
)
async def list_roles(
    db: DBSession,
) -> list[RoleResponse]:
    repository = RoleRepository(db)

    return await repository.list_all()


@router.get(
    "/{role_id}",
    response_model=RoleResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtém uma role",
    dependencies=[
        Depends(
            require_permissions("roles:read")
        )
    ],
)
async def get_role(
    role_id: UUID,
    db: DBSession,
) -> RoleResponse:
    repository = RoleRepository(db)

    role = await repository.get_by_id(
        role_id
    )

    if role is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role não encontrada.",
        )

    return role


@router.put(
    "/{role_id}",
    response_model=RoleResponse,
    status_code=status.HTTP_200_OK,
    summary="Atualiza uma role",
    dependencies=[
        Depends(
            require_permissions("roles:update")
        )
    ],
)
async def update_role(
    role_id: UUID,
    data: RoleUpdateRequest,
    db: DBSession,
) -> RoleResponse:
    repository = RoleRepository(db)

    role = await repository.get_by_id(
        role_id
    )

    if role is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role não encontrada.",
        )

    if data.name is not None:
        name = data.name.strip().lower()

        if await repository.exists_by_name(
            name,
            exclude_role_id=role.id,
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Role já cadastrada.",
            )

        role.name = name

    if data.description is not None:
        role.description = data.description

    if data.is_active is not None:
        role.is_active = data.is_active

    await repository.update(role)

    await db.commit()

    return role


@router.delete(
    "/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove uma role",
    dependencies=[
        Depends(
            require_permissions("roles:delete")
        )
    ],
)
async def delete_role(
    role_id: UUID,
    db: DBSession,
) -> None:
    repository = RoleRepository(db)

    role = await repository.get_by_id(
        role_id
    )

    if role is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role não encontrada.",
        )

    await repository.delete(role)

    await db.commit()


@router.put(
    "/{role_id}/permissions",
    response_model=RoleResponse,
    status_code=status.HTTP_200_OK,
    summary="Atualiza as permissões de uma role",
    dependencies=[
        Depends(
            require_permissions("roles:update")
        )
    ],
)
async def update_role_permissions(
    role_id: UUID,
    data: RolePermissionsRequest,
    db: DBSession,
) -> RoleResponse:
    repository = RoleRepository(db)

    role = await repository.get_by_id(
        role_id
    )

    if role is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role não encontrada.",
        )

    permissions = (
        await repository.get_permissions_by_ids(
            data.permission_ids
        )
    )

    if len(permissions) != len(
        set(data.permission_ids)
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Uma ou mais permissões "
                "não foram encontradas."
            ),
        )

    await repository.add_permissions(
        role,
        permissions,
    )

    await db.commit()

    return role


@router.get(
    "/permissions/all",
    response_model=list[PermissionResponse],
    status_code=status.HTTP_200_OK,
    summary="Lista todas as permissões",
    dependencies=[
        Depends(
            require_permissions("roles:read")
        )
    ],
)
async def list_permissions(
    db: DBSession,
) -> list[PermissionResponse]:
    repository = RoleRepository(db)

    return await repository.get_all_permissions()