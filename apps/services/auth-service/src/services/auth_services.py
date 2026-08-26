from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import verify_password
from src.models.user import User
from src.repositories.user_repository import UserRepository


class AuthService:

    def __init__(self, session: AsyncSession):
        self.repository = UserRepository(session)

    async def authenticate(
        self,
        email: str,
        password: str,
    ) -> User | None:
        user = await self.repository.get_by_email(email)

        if user is None:
            return None

        if not user.is_active:
            return None

        if not verify_password(
            password,
            user.password_hash,
        ):
            return None

        return user