import time
import uuid

from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.logging import logger


class RequestLoggingMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get(
            "X-Request-ID",
            str(uuid.uuid4()),
        )

        request.state.request_id = request_id

        started_at = time.perf_counter()

        try:
            response = await call_next(request)

            duration_ms = (
                time.perf_counter() - started_at
            ) * 1000

            response.headers["X-Request-ID"] = request_id

            logger.info(
                "HTTP request completed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration_ms, 2),
                },
            )

            return response

        except Exception:
            duration_ms = (
                time.perf_counter() - started_at
            ) * 1000

            logger.exception(
                "HTTP request failed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": round(duration_ms, 2),
                },
            )

            raise


def configure_logging(app: FastAPI) -> None:
    app.add_middleware(RequestLoggingMiddleware)