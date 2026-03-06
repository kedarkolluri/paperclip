"""Private hostname guard – restricts access by Host header."""

from __future__ import annotations

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

_LOOPBACK = frozenset({"localhost", "127.0.0.1", "::1"})


class PrivateHostnameGuardMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, *, allowed_hostnames: set[str] | None = None, enabled: bool = False):
        super().__init__(app)
        self.allowed = allowed_hostnames or set()
        self.enabled = enabled

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if not self.enabled:
            return await call_next(request)

        host = (request.headers.get("x-forwarded-host") or request.headers.get("host") or "").split(":")[0]
        if host in _LOOPBACK or host in self.allowed:
            return await call_next(request)

        return Response(
            content='{"error":"Hostname not allowed"}',
            status_code=403,
            media_type="application/json",
        )
