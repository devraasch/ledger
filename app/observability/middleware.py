import time
from collections.abc import Awaitable, Callable
from uuid import uuid4

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.observability.logging import get_logger
from app.observability.metrics import (
    HTTP_REQUEST_DURATION_SECONDS,
    HTTP_REQUESTS_TOTAL,
)

REQUEST_ID_HEADER = "X-Request-ID"


class RequestObservabilityMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = request.headers.get(REQUEST_ID_HEADER, str(uuid4()))
        path = request.url.path
        method = request.method
        start_time = time.perf_counter()
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        logger = get_logger()
        try:
            response = await call_next(request)
        except Exception as exc:
            duration_ms = _duration_ms(start_time)
            HTTP_REQUESTS_TOTAL.labels(
                method=method,
                path=path,
                status_code="500",
            ).inc()
            HTTP_REQUEST_DURATION_SECONDS.labels(method=method, path=path).observe(
                duration_ms / 1000
            )
            logger.error(
                "request_failed",
                operation="http_request",
                method=method,
                path=path,
                status_code=500,
                duration_ms=duration_ms,
                error_type=type(exc).__name__,
            )
            raise

        duration_ms = _duration_ms(start_time)
        response.headers[REQUEST_ID_HEADER] = request_id
        HTTP_REQUESTS_TOTAL.labels(
            method=method,
            path=path,
            status_code=str(response.status_code),
        ).inc()
        HTTP_REQUEST_DURATION_SECONDS.labels(method=method, path=path).observe(
            duration_ms / 1000
        )
        logger.info(
            "request_completed",
            operation="http_request",
            method=method,
            path=path,
            status_code=response.status_code,
            duration_ms=duration_ms,
        )
        structlog.contextvars.clear_contextvars()
        return response


def _duration_ms(start_time: float) -> float:
    return round((time.perf_counter() - start_time) * 1000, 2)
