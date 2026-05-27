"""Typed configuration for external ingest sources."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


class GoogleDriveSourceConfig(BaseModel):
    """Configuration for reading CSV exports from one shared Google Drive folder."""

    source_id: str
    source_type: Literal["google_drive"] = "google_drive"
    client_key: str
    system_key: str
    environment: str = "test"
    repository_root_id: str | None = None
    auth_mode: Literal["user_oauth", "service_account"] = "user_oauth"
    folder_id_env: str
    client_secrets_path_env: str | None = None
    token_path_env: str | None = None
    service_account_path_env: str | None = None
    scopes: list[str] = Field(default_factory=lambda: ["https://www.googleapis.com/auth/drive"])
    destination_path: Path
    file_name_patterns: list[str] = Field(default_factory=lambda: ["*.csv"])
    archive_after_download: bool = False

    def folder_id(self) -> str:
        """Return the configured Drive folder id from the environment."""

        return _required_env(self.folder_id_env)

    def client_secrets_path(self) -> Path | None:
        """Return the local OAuth client-secrets path when configured."""

        return _optional_env_path(self.client_secrets_path_env)

    def token_path(self) -> Path | None:
        """Return the local OAuth token path when configured."""

        return _optional_env_path(self.token_path_env)

    def service_account_path(self) -> Path | None:
        """Return the service-account credential path when configured."""

        return _optional_env_path(self.service_account_path_env)


class ClientIngestSourceConfig(BaseModel):
    """All external ingest sources for one client namespace."""

    client_key: str
    sources: list[GoogleDriveSourceConfig]

    def get_source(self, source_id: str) -> GoogleDriveSourceConfig:
        """Return one configured source by id."""

        for source in self.sources:
            if source.source_id == source_id:
                return source
        raise KeyError(f"Unknown ingest source: {source_id}")


def load_client_ingest_config(path: Path) -> ClientIngestSourceConfig:
    """Load a client ingest-source config file."""

    return ClientIngestSourceConfig.model_validate(json.loads(path.read_text(encoding="utf-8")))


class RepositoryRootConfig(BaseModel):
    """Client-owned repository root for one environment."""

    root_id: str
    environment: str
    repository_type: Literal["local", "google_drive", "gcs", "database"]
    root_ref_env: str

    def root_ref(self) -> str:
        """Return the configured repository root reference from the environment."""

        return _required_env(self.root_ref_env)


class SourceLayerConfig(BaseModel):
    """Landing-zone configuration for one client source system."""

    source_system: str
    environment: str
    root_id: str
    landing_prefix: str

    @property
    def incoming_prefix(self) -> str:
        return f"{self.landing_prefix.rstrip('/')}/incoming"

    @property
    def archive_prefix(self) -> str:
        return f"{self.landing_prefix.rstrip('/')}/archive"

    @property
    def rejected_prefix(self) -> str:
        return f"{self.landing_prefix.rstrip('/')}/rejected"


class EdwLayerConfig(BaseModel):
    """Client-level EDW output prefixes for one environment."""

    environment: str
    root_id: str
    prefixes: dict[str, str]


class ClientDataLayerConfig(BaseModel):
    """Repository roots, source landing layers, and EDW layers for one client."""

    client_key: str
    repository_roots: list[RepositoryRootConfig]
    source_layers: list[SourceLayerConfig]
    edw_layers: list[EdwLayerConfig]

    def source_layer(self, source_system: str, environment: str) -> SourceLayerConfig:
        """Return the source landing layer for a source system/environment."""

        for layer in self.source_layers:
            if layer.source_system == source_system and layer.environment == environment:
                return layer
        raise KeyError(f"Unknown source layer: {source_system}/{environment}")

    def edw_layer(self, environment: str) -> EdwLayerConfig:
        """Return the client-level EDW layer for an environment."""

        for layer in self.edw_layers:
            if layer.environment == environment:
                return layer
        raise KeyError(f"Unknown EDW layer: {environment}")

    def repository_root(self, root_id: str) -> RepositoryRootConfig:
        """Return a repository root by id."""

        for root in self.repository_roots:
            if root.root_id == root_id:
                return root
        raise KeyError(f"Unknown repository root: {root_id}")


def load_client_data_layer_config(path: Path) -> ClientDataLayerConfig:
    """Load a client data-layer config file."""

    return ClientDataLayerConfig.model_validate(json.loads(path.read_text(encoding="utf-8")))


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _optional_env_path(name: str | None) -> Path | None:
    if not name:
        return None
    value = os.getenv(name, "").strip()
    return Path(value) if value else None
