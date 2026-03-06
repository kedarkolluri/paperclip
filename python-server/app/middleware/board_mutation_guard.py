"""CSRF / origin protection for board mutations."""

from __future__ import annotations

from urllib.parse import urlparse

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint


_SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})


class BoardMutationGuardMiddleware(BaseHTTPMiddleware):
    """Prevents CSRF on mutation endpoints by validating Origin/Referer."""

    def __init__(self, app, *, allowed_origins: list[str] | None = None):
        super().__init__(app)
        self.allowed_origins = set(allowed_origins or [])

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method in _SAFE_METHODS:
            return await call_next(request)

        # Agent requests bypass CSRF
        auth = request.headers.get("authorization", "")
        if auth.startswith("Bearer pk_") or auth.startswith("Bearer ey"):
            return await call_next(request)

        origin = request.headers.get("origin") or request.headers.get("referer")
        if origin:
            parsed = urlparse(origin)
            host = f"{parsed.scheme}://{parsed.hostname}"
            if parsed.port:
                host += f":{parsed.port}"
            if host not in self.allowed_origins and parsed.hostname not in ("localhost", "127.0.0.1", "::1"):
                return Response(content='{"error":"Origin not trusted"}', status_code=403, media_type="application/json")

        return await call_next(request)
