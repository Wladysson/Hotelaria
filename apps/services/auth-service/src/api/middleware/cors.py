from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings


def setup_cors(app: FastAPI) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_methods_list,
        allow_headers=settings.cors_headers_list,
    )