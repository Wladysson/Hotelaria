from sqlalchemy.exc import IntegrityError

from app.core.exceptions import (
    UserAlreadyExistsError,
    UserNotFoundError,
)
from app.core.security import hash_password
from app.models.usuario import Usuario
from app.repositories.usuario_repository import UsuarioRepository
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate


class UsuarioService:
    def __init__(
        self,
        usuario_repository: UsuarioRepository,
    ) -> None:
        self.usuario_repository = usuario_repository

    async def create(
        self,
        data: UsuarioCreate,
    ) -> Usuario:
        email = data.email.lower()

        existing_user = await self.usuario_repository.get_by_email(email)

        if existing_user is not None:
            raise UserAlreadyExistsError()

        usuario = Usuario(
            nome=data.nome.strip(),
            email=email,
            password_hash=hash_password(data.password),
            is_admin=False,
            is_active=True,
        )

        try:
            usuario = await self.usuario_repository.create(usuario)
            await self.usuario_repository.db.commit()
        except IntegrityError:
            await self.usuario_repository.db.rollback()
            raise UserAlreadyExistsError()

        return usuario

    async def get_by_id(
        self,
        usuario_id: int,
    ) -> Usuario:
        usuario = await self.usuario_repository.get_by_id(usuario_id)

        if usuario is None:
            raise UserNotFoundError()

        return usuario

    async def update(
        self,
        usuario_id: int,
        data: UsuarioUpdate,
    ) -> Usuario:
        usuario = await self.get_by_id(usuario_id)

        if data.nome is not None:
            usuario.nome = data.nome.strip()

        if data.email is not None:
            email = data.email.lower()

            if email != usuario.email:
                existing_user = (
                    await self.usuario_repository.get_by_email(email)
                )

                if (
                    existing_user is not None
                    and existing_user.id != usuario.id
                ):
                    raise UserAlreadyExistsError()

                usuario.email = email

        if data.password is not None:
            usuario.password_hash = hash_password(data.password)

        try:
            usuario = await self.usuario_repository.update(usuario)
            await self.usuario_repository.db.commit()
        except IntegrityError:
            await self.usuario_repository.db.rollback()
            raise UserAlreadyExistsError()

        return usuario