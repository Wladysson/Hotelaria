from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import hash_password
from src.models.user import User
from src.repositories.user_repository import UserRepository
from src.schemas.user import UserCreate, UserResponse, UserUpdate


class UserService:

    def __init__(self, session: AsyncSession) -> None:
        self.user_repository = UserRepository(session)

    async def create_user(self, data: UserCreate) -> UserResponse:
        email = data.email.lower()

        if await self.user_repository.exists_by_email(email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email is already registered",
            )

        user = User(
            email=email,
            full_name=data.full_name,
            password_hash=hash_password(data.password),
        )

        user = await self.user_repository.create(user)

        return UserResponse.model_validate(user)

    async def get_user(self, user_id) -> UserResponse:
        user = await self.user_repository.get_by_id(user_id)

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        return UserResponse.model_validate(user)

    async def update_user(
        self,
        user_id,
        data: UserUpdate,
    ) -> UserResponse:
        user = await self.user_repository.get_by_id(user_id)

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        if data.email is not None:
            email = data.email.lower()

            if email != user.email:
                if await self.user_repository.exists_by_email(email):
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Email is already registered",
                    )

                user.email = email

        if data.full_name is not None:
            user.full_name = data.full_name

        user = await self.user_repository.update(user)

        return UserResponse.model_validate(user)