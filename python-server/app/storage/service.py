"""Storage service – handles file uploads with path generation and hashing."""

from __future__ import annotations

import hashlib
import re
import uuid
from datetime import datetime, timezone

from app.storage.providers import StorageProvider


def _sanitize_namespace(ns: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]", "_", ns)[:64]


class StorageService:
    def __init__(self, provider: StorageProvider, provider_name: str = "local_disk") -> None:
        self.provider = provider
        self.provider_name = provider_name

    async def upload(
        self,
        company_id: uuid.UUID,
        data: bytes,
        content_type: str,
        *,
        original_filename: str | None = None,
        namespace: str = "assets",
    ) -> dict:
        """Upload a file and return metadata."""
        now = datetime.now(timezone.utc)
        sha = hashlib.sha256(data).hexdigest()
        ext = _extension_for(content_type)
        ns = _sanitize_namespace(namespace)

        object_key = (
            f"companies/{company_id}/{ns}/"
            f"{now.strftime('%Y/%m/%d')}/"
            f"{uuid.uuid4().hex}{ext}"
        )

        await self.provider.put(object_key, data, content_type)

        return {
            "provider": self.provider_name,
            "object_key": object_key,
            "content_type": content_type,
            "byte_size": len(data),
            "sha256": sha,
            "original_filename": original_filename,
        }

    async def download(self, object_key: str) -> bytes | None:
        return await self.provider.get(object_key)

    async def delete(self, object_key: str) -> None:
        await self.provider.delete(object_key)

    def validate_company_access(self, object_key: str, company_id: uuid.UUID) -> bool:
        return object_key.startswith(f"companies/{company_id}/")


def _extension_for(content_type: str) -> str:
    mapping = {
        "image/png": ".png",
        "image/jpeg": ".jpg",
        "image/jpg": ".jpg",
        "image/webp": ".webp",
        "image/gif": ".gif",
    }
    return mapping.get(content_type, "")
