from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.usuario import Usuario


class UsuarioRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, usuario_id: int) -> Usuario | None:
        result = await self.db.execute(
            select(Usuario).where(Usuario.id == usuario_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Usuario | None:
        result = await self.db.execute(
            select(Usuario).where(Usuario.email == email.lower())
        )
        return result.scalar_one_or_none()

    async def create(self, usuario: Usuario) -> Usuario:
        self.db.add(usuario)

        await self.db.flush()
        await self.db.refresh(usuario)

        return usuario

    async def update(self, usuario: Usuario) -> Usuario:
        await self.db.flush()
        await self.db.refresh(usuario)

        return usuario

    async def delete(self, usuario: Usuario) -> None:
        await self.db.delete(usuario)
        await self.db.flush()