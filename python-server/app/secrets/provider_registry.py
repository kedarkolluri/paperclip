"""Secret provider registry."""

from __future__ import annotations

from typing import Protocol

from app.config import AppConfig
from app.secrets.encryption import LocalEncryptedProvider


class SecretProvider(Protocol):
    def encrypt(self, plaintext: str) -> dict: ...
    def decrypt(self, material: dict) -> str: ...
    def value_sha256(self, plaintext: str) -> str: ...


_EXTERNAL_STUBS = ("aws_sm", "gcp_sm", "vault")


class ExternalStubProvider:
    """Placeholder for external secret managers (not yet implemented)."""

    def __init__(self, provider_id: str) -> None:
        self.provider_id = provider_id

    def encrypt(self, plaintext: str) -> dict:
        raise NotImplementedError(f"External provider '{self.provider_id}' is not configured")

    def decrypt(self, material: dict) -> str:
        raise NotImplementedError(f"External provider '{self.provider_id}' is not configured")

    def value_sha256(self, plaintext: str) -> str:
        import hashlib
        return hashlib.sha256(plaintext.encode()).hexdigest()


def get_provider(config: AppConfig) -> SecretProvider:
    """Get the secret provider based on config."""
    if config.secrets.provider == "local_encrypted":
        return LocalEncryptedProvider(
            master_key=config.secrets.master_key,
            master_key_file=config.secrets.master_key_file,
        )
    return ExternalStubProvider(config.secrets.provider)


def list_providers() -> list[dict]:
    return [
        {"id": "local_encrypted", "label": "Local Encrypted (AES-256-GCM)", "available": True},
        {"id": "aws_sm", "label": "AWS Secrets Manager", "available": False},
        {"id": "gcp_sm", "label": "GCP Secret Manager", "available": False},
        {"id": "vault", "label": "HashiCorp Vault", "available": False},
    ]
