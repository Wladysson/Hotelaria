from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.deps import (
    AuthServiceDependency,
    CurrentUser,
    TokenServiceDependency,
    UserServiceDependency,
)
from src.core.jwt import JWTError
from src.schemas.auth import (
    AuthenticationResponse,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    LogoutRequest,
    LogoutResponse,
    MessageResponse,
    RefreshTokenRequest,
    ResendVerificationRequest,
    ResetPasswordRequest,
    VerifyEmailRequest,
)
from src.schemas.user import UserResponse


router = APIRouter()


@router.post(
    "/login",
    response_model=AuthenticationResponse,
    status_code=status.HTTP_200_OK,
    summary="Realiza autenticação do usuário",
)
async def login(
    credentials: LoginRequest,
    auth_service: AuthServiceDependency,
) -> AuthenticationResponse:
    return await auth_service.authenticate(
        credentials
    )


@router.post(
    "/refresh",
    response_model=AuthenticationResponse,
    status_code=status.HTTP_200_OK,
    summary="Renova os tokens de autenticação",
)
async def refresh_token(
    data: RefreshTokenRequest,
    auth_service: AuthServiceDependency,
) -> AuthenticationResponse:
    return await auth_service.refresh_access_token(
        data.refresh_token
    )


@router.post(
    "/logout",
    response_model=LogoutResponse,
    status_code=status.HTTP_200_OK,
    summary="Encerra a sessão atual",
)
async def logout(
    data: LogoutRequest,
    current_user: CurrentUser,
) -> LogoutResponse:
    return LogoutResponse(
        message="Sessão encerrada com sucesso."
    )


@router.post(
    "/logout-all",
    response_model=LogoutResponse,
    status_code=status.HTTP_200_OK,
    summary="Encerra todas as sessões do usuário",
)
async def logout_all(
    current_user: CurrentUser,
) -> LogoutResponse:
    return LogoutResponse(
        message="Todas as sessões foram encerradas."
    )


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtém o usuário autenticado",
)
async def get_authenticated_user(
    current_user: CurrentUser,
) -> UserResponse:
    return current_user


@router.post(
    "/change-password",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Altera a senha do usuário autenticado",
)
async def change_password(
    data: ChangePasswordRequest,
    current_user: CurrentUser,
    auth_service: AuthServiceDependency,
) -> MessageResponse:
    if data.new_password != data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A confirmação da nova senha não corresponde.",
        )

    await auth_service.change_password(
        user=current_user,
        current_password=data.current_password,
        new_password=data.new_password,
    )

    return MessageResponse(
        message="Senha alterada com sucesso."
    )


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Solicita recuperação de senha",
)
async def forgot_password(
    data: ForgotPasswordRequest,
    user_service: UserServiceDependency,
    token_service: TokenServiceDependency,
) -> MessageResponse:
    try:
        user = await user_service.get_user_by_email(
            str(data.email)
        )

        await token_service.create_password_reset_token(
            user
        )

    except HTTPException:
        pass

    return MessageResponse(
        message=(
            "Se o e-mail estiver cadastrado, "
            "as instruções de recuperação serão enviadas."
        )
    )


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Redefine a senha através do token",
)
async def reset_password(
    data: ResetPasswordRequest,
    user_service: UserServiceDependency,
    token_service: TokenServiceDependency,
    auth_service: AuthServiceDependency,
) -> MessageResponse:
    if data.new_password != data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A confirmação da nova senha não corresponde.",
        )

    try:
        user_id = token_service.validate_password_reset_token(
            data.token
        )
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    user = await user_service.get_user(user_id)

    await auth_service.reset_password(
        user=user,
        new_password=data.new_password,
    )

    return MessageResponse(
        message="Senha redefinida com sucesso."
    )


@router.post(
    "/verify-email",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Confirma o endereço de e-mail",
)
async def verify_email(
    data: VerifyEmailRequest,
    user_service: UserServiceDependency,
    token_service: TokenServiceDependency,
) -> MessageResponse:
    try:
        user_id = token_service.validate_email_verification_token(
            data.token
        )
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    user = await user_service.get_user(user_id)

    await user_service.verify_user(user)

    return MessageResponse(
        message="E-mail verificado com sucesso."
    )


@router.post(
    "/resend-verification",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Solicita novo token de verificação",
)
async def resend_verification(
    data: ResendVerificationRequest,
    user_service: UserServiceDependency,
    token_service: TokenServiceDependency,
) -> MessageResponse:
    try:
        user = await user_service.get_user_by_email(
            str(data.email)
        )

        if not user.is_verified:
            await token_service.create_email_verification_token(
                user
            )

    except HTTPException:
        pass

    return MessageResponse(
        message=(
            "Se o e-mail estiver cadastrado e ainda não "
            "verificado, um novo token será enviado."
        )
    )