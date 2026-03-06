"""Global error handling middleware."""

from __future__ import annotations

import logging
import traceback

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

logger = logging.getLogger("paperclip.errors")


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        try:
            return await call_next(request)
        except ValidationError as exc:
            return JSONResponse(
                status_code=422,
                content={"error": "Validation error", "details": exc.errors()},
            )
        except Exception as exc:
            status = getattr(exc, "status_code", 500)
            if isinstance(status, int) and 400 <= status < 500:
                return JSONResponse(
                    status_code=status,
                    content={"error": str(exc)},
                )
            logger.error(
                "Unhandled error on %s %s: %s",
                request.method,
                request.url.path,
                exc,
                exc_info=True,
            )
            return JSONResponse(
                status_code=500,
                content={"error": "Internal server error"},
            )
