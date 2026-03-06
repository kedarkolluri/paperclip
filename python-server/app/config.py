"""Application configuration loaded from environment variables and config files."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings


def _home_dir() -> Path:
    return Path(os.environ.get("PAPERCLIP_HOME", Path.home() / ".paperclip"))


class DatabaseConfig(BaseSettings):
    model_config = {"env_prefix": "PAPERCLIP_DB_"}

    mode: Literal["embedded", "external"] = "embedded"
    url: str = ""
    embedded_port: int = 5499
    auto_migrate: bool = True
    migration_prompt: Literal["ask", "auto", "never"] = "auto"

    @property
    def effective_url(self) -> str:
        if self.url:
            return self.url
        return f"postgresql+asyncpg://paperclip:paperclip@localhost:{self.embedded_port}/paperclip"


class StorageConfig(BaseSettings):
    model_config = {"env_prefix": "PAPERCLIP_STORAGE_"}

    provider: Literal["local_disk", "s3"] = "local_disk"
    local_dir: str = ""
    s3_bucket: str = ""
    s3_prefix: str = ""
    s3_endpoint: str = ""
    s3_region: str = "us-east-1"
    attachment_max_bytes: int = 10 * 1024 * 1024  # 10 MB

    @property
    def effective_local_dir(self) -> str:
        return self.local_dir or str(_home_dir() / "storage")


class SecretsConfig(BaseSettings):
    model_config = {"env_prefix": "PAPERCLIP_SECRETS_"}

    provider: Literal["local_encrypted", "aws_sm", "gcp_sm", "vault"] = "local_encrypted"
    master_key: str = ""
    master_key_file: str = ""
    strict: bool = False


class AuthConfig(BaseSettings):
    model_config = {"env_prefix": "PAPERCLIP_AUTH_"}

    base_url: str = ""
    trusted_origins: list[str] = Field(default_factory=list)
    jwt_secret: str = ""
    jwt_ttl_hours: int = 48


class HeartbeatConfig(BaseSettings):
    model_config = {"env_prefix": "PAPERCLIP_HEARTBEAT_"}

    enabled: bool = True
    interval_seconds: int = 30
    max_concurrent: int = 5
    cooldown_seconds: int = 10


class AppConfig(BaseSettings):
    """Root application configuration."""

    model_config = {"env_prefix": "PAPERCLIP_"}

    deployment_mode: Literal["local_trusted", "authenticated"] = "local_trusted"
    deployment_exposure: Literal["private", "public"] = "private"
    host: str = "127.0.0.1"
    port: int = 3100
    serve_ui: bool = True
    ui_dist_dir: str = ""
    log_level: str = "info"
    log_dir: str = ""
    allowed_hostnames: list[str] = Field(default_factory=list)
    company_deletion_enabled: bool = False

    db: DatabaseConfig = Field(default_factory=DatabaseConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    secrets: SecretsConfig = Field(default_factory=SecretsConfig)
    auth: AuthConfig = Field(default_factory=AuthConfig)
    heartbeat: HeartbeatConfig = Field(default_factory=HeartbeatConfig)

    @classmethod
    def load(cls) -> "AppConfig":
        """Load config from env + optional config file."""
        config_path = _home_dir() / "config.json"
        file_overrides: dict = {}
        if config_path.exists():
            file_overrides = json.loads(config_path.read_text())
        return cls(**file_overrides)
