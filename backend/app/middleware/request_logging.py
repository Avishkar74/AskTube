"""Starlette middleware to attach request IDs and log latency.

Adds/propagates an `X-Request-ID` header and logs a concise line per request
including method, path, status, and duration in milliseconds. Exceptions are
logged with the same request ID for correlation in logs.
"""

import time
import uuid
from typing import Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from ..core.logging import logger


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Attach a request ID and log basic request/response with latency.

    - Reads `X-Request-ID` or `X-Correlation-ID` if provided by client.
    - Generates a UUID4 if none provided.
    - Adds `X-Request-ID` to the response headers.
    - Logs start and completion with method, path, status, and duration_ms.
    """

    def __init__(self, app, header_name: str = "X-Request-ID") -> None:
        super().__init__(app)
        self.header_name = header_name

    async def dispatch(self, request: Request, call_next: Callable[[Request], Response]) -> Response:
        start = time.perf_counter()

        incoming_request_id = (
            request.headers.get(self.header_name)
            or request.headers.get("X-Correlation-ID")
        )
        request_id = incoming_request_id or str(uuid.uuid4())
        # expose on request.state for handlers if needed
        request.state.request_id = request_id

        method = request.method
        path = request.url.path
        client = request.client.host if request.client else "-"
        ua = request.headers.get("user-agent", "-")

        logger.info(f"{request_id} -> {method} {path} from {client} ua='{ua}'")

        try:
            response = await call_next(request)
        except Exception as exc:  # log exceptions with the same request id
            duration_ms = int((time.perf_counter() - start) * 1000)
            logger.exception(f"{request_id} !! {method} {path} raised after {duration_ms}ms: {exc}")
            raise

        duration_ms = int((time.perf_counter() - start) * 1000)
        response.headers[self.header_name] = request_id
        logger.info(f"{request_id} <- {method} {path} {response.status_code} {duration_ms}ms")
        return response
