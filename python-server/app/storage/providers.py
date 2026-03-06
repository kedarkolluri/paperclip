"""Storage provider implementations."""

from __future__ import annotations

import hashlib
import os
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class StorageProvider(ABC):
    @abstractmethod
    async def put(self, key: str, data: bytes, content_type: str) -> None: ...

    @abstractmethod
    async def get(self, key: str) -> bytes | None: ...

    @abstractmethod
    async def delete(self, key: str) -> None: ...


class LocalDiskProvider(StorageProvider):
    def __init__(self, base_dir: str) -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    async def put(self, key: str, data: bytes, content_type: str) -> None:
        path = self.base_dir / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    async def get(self, key: str) -> bytes | None:
        path = self.base_dir / key
        if path.exists():
            return path.read_bytes()
        return None

    async def delete(self, key: str) -> None:
        path = self.base_dir / key
        if path.exists():
            path.unlink()


class S3Provider(StorageProvider):
    def __init__(self, bucket: str, prefix: str = "", region: str = "us-east-1", endpoint: str = "") -> None:
        import boto3
        kwargs: dict[str, Any] = {"region_name": region}
        if endpoint:
            kwargs["endpoint_url"] = endpoint
        self.s3 = boto3.client("s3", **kwargs)
        self.bucket = bucket
        self.prefix = prefix

    def _full_key(self, key: str) -> str:
        return f"{self.prefix}/{key}" if self.prefix else key

    async def put(self, key: str, data: bytes, content_type: str) -> None:
        self.s3.put_object(Bucket=self.bucket, Key=self._full_key(key), Body=data, ContentType=content_type)

    async def get(self, key: str) -> bytes | None:
        try:
            resp = self.s3.get_object(Bucket=self.bucket, Key=self._full_key(key))
            return resp["Body"].read()
        except self.s3.exceptions.NoSuchKey:
            return None

    async def delete(self, key: str) -> None:
        self.s3.delete_object(Bucket=self.bucket, Key=self._full_key(key))
