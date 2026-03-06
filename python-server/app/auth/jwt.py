"""Agent JWT authentication (HS256)."""

from __future__ import annotations

import hashlib
import hmac
import time
import uuid
from typing import Any

from jose import jwt, JWTError

from app.config import AppConfig

_ALGORITHM = "HS256"
_DEFAULT_TTL = 48 * 3600  # 48 hours


def _get_secret(config: AppConfig) -> str:
    secret = config.auth.jwt_secret
    if not secret:
        secret = "paperclip-dev-secret-do-not-use-in-production"
    return secret


def create_agent_jwt(
    config: AppConfig,
    *,
    agent_id: uuid.UUID,
    company_id: uuid.UUID,
    adapter_type: str,
    run_id: uuid.UUID | None = None,
) -> str:
    """Create a JWT for agent-to-server authentication."""
    now = int(time.time())
    claims: dict[str, Any] = {
        "sub": str(agent_id),
        "company_id": str(company_id),
        "adapter_type": adapter_type,
        "iat": now,
        "exp": now + (config.auth.jwt_ttl_hours * 3600 or _DEFAULT_TTL),
    }
    if run_id:
        claims["run_id"] = str(run_id)
    return jwt.encode(claims, _get_secret(config), algorithm=_ALGORITHM)


def verify_agent_jwt(config: AppConfig, token: str) -> dict[str, Any] | None:
    """Verify and decode an agent JWT. Returns claims or None."""
    try:
        claims = jwt.decode(token, _get_secret(config), algorithms=[_ALGORITHM])
        return claims
    except JWTError:
        return None


def hash_api_key(raw_key: str) -> str:
    """SHA-256 hash of a raw API key."""
    return hashlib.sha256(raw_key.encode()).hexdigest()


def generate_api_key() -> tuple[str, str]:
    """Generate a (raw_key, key_hash) pair."""
    raw = f"pk_{uuid.uuid4().hex}"
    return raw, hash_api_key(raw)
