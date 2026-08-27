import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


logger = logging.getLogger("hotel-service.http")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Registra informações de cada requisição HTTP.
    """

    async def dispatch(
        self,
        request: Request,
        call_next,
    ) -> Response:
        request_id = request.headers.get(
            "X-Request-ID",
            str(uuid.uuid4()),
        )

        request.state.request_id = request_id

        start_time = time.perf_counter()

        try:
            response = await call_next(request)

            duration_ms = (
                time.perf_counter() - start_time
            ) * 1000

            response.headers["X-Request-ID"] = request_id

            logger.info(
                "%s %s | status=%s | duration_ms=%.2f | request_id=%s",
                request.method,
                request.url.path,
                response.status_code,
                duration_ms,
                request_id,
            )

            return response

        except Exception:
            duration_ms = (
                time.perf_counter() - start_time
            ) * 1000

            logger.exception(
                "%s %s | status=500 | duration_ms=%.2f | request_id=%s",
                request.method,
                request.url.path,
                duration_ms,
                request_id,
            )

            raise