from fastapi import Header, HTTPException, status


async def get_current_user(
    authorization: str | None = Header(default=None),
) -> dict[str, object]:
    """
    Obtém a identidade do usuário autenticado.

    A validação definitiva do JWT será realizada
    pela camada de autenticação da plataforma.
    """

    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticação não informado.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Esquema de autenticação inválido.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    token = authorization.removeprefix("Bearer ").strip()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticação inválido.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    return {
        "authenticated": True,
        "token": token,
    }