"""Repository factory for configured client data roots."""

from __future__ import annotations

from pathlib import Path

from iceflo_signal.config.ingest_sources import GoogleDriveSourceConfig, RepositoryRootConfig
from iceflo_signal.ingestion.google_auth import build_google_credentials
from iceflo_signal.storage.gcs_repository import GcsObjectRepository
from iceflo_signal.storage.google_drive_repository import GoogleApiDriveObjectClient, GoogleDriveObjectRepository
from iceflo_signal.storage.repositories import LocalFileRepository, ObjectRepository


def build_repository(
    repository_root: RepositoryRootConfig,
    *,
    local_storage_root: Path = Path("storage_sample"),
    google_drive_source: GoogleDriveSourceConfig | None = None,
) -> ObjectRepository:
    """Create the repository implementation described by a client data root."""

    if repository_root.repository_type == "local":
        return LocalFileRepository(Path(repository_root.root_ref()))

    if repository_root.repository_type == "gcs":
        return GcsObjectRepository.from_root_ref(repository_root.root_ref())

    if repository_root.repository_type == "google_drive":
        if not google_drive_source:
            raise ValueError("Google Drive repositories require a Google Drive source config for credentials.")
        credentials = build_google_credentials(google_drive_source)
        return GoogleDriveObjectRepository(GoogleApiDriveObjectClient(credentials, repository_root.root_ref()))

    if repository_root.repository_type == "database":
        raise NotImplementedError("Database-backed repositories are not implemented yet.")

    return LocalFileRepository(local_storage_root)
