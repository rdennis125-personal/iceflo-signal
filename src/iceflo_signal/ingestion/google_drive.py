"""Google Drive ingestion helpers for shared client folders."""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from iceflo_signal.config.ingest_sources import GoogleDriveSourceConfig


@dataclass(frozen=True)
class DriveFile:
    """Metadata for a file available from Google Drive."""

    file_id: str
    name: str
    mime_type: str
    modified_time: str | None = None


@dataclass(frozen=True)
class DownloadedDriveFile:
    """Local result from downloading one Drive file into the landing zone."""

    drive_file: DriveFile
    local_path: Path


class DriveClient(Protocol):
    """Minimal Drive API surface used by the ingest source."""

    def list_files(self, folder_id: str) -> list[DriveFile]:
        """List files in a Drive folder."""

    def download_file(self, file_id: str, destination_path: Path) -> None:
        """Download one Drive file to the requested local path."""


class GoogleDriveIngestSource:
    """Download configured CSV exports from a Google Drive folder into landing."""

    def __init__(self, config: GoogleDriveSourceConfig, drive_client: DriveClient) -> None:
        self._config = config
        self._drive_client = drive_client

    def sync(self) -> list[DownloadedDriveFile]:
        """Download matching files from Google Drive into the configured landing folder."""

        folder_id = self._config.folder_id()
        destination_dir = self._config.destination_path
        destination_dir.mkdir(parents=True, exist_ok=True)

        downloaded: list[DownloadedDriveFile] = []
        for drive_file in self._drive_client.list_files(folder_id):
            if not _matches_any(drive_file.name, self._config.file_name_patterns):
                continue
            local_path = destination_dir / drive_file.name
            self._drive_client.download_file(drive_file.file_id, local_path)
            downloaded.append(DownloadedDriveFile(drive_file=drive_file, local_path=local_path))

        return downloaded


class GoogleApiDriveClient:
    """Drive client backed by Google's Python API libraries."""

    def __init__(self, credentials: object) -> None:
        try:
            from googleapiclient.discovery import build
            from googleapiclient.http import MediaIoBaseDownload
        except ImportError as exc:
            raise RuntimeError(
                "Google Drive ingestion requires google-api-python-client. "
                "Install project requirements before using Drive sync."
            ) from exc

        self._service = build("drive", "v3", credentials=credentials)
        self._downloader_class = MediaIoBaseDownload

    def list_files(self, folder_id: str) -> list[DriveFile]:
        """List non-trashed files immediately inside a folder."""

        query = f"'{folder_id}' in parents and trashed = false"
        response = (
            self._service.files()
            .list(
                q=query,
                fields="files(id,name,mimeType,modifiedTime)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
            )
            .execute()
        )
        return [
            DriveFile(
                file_id=item["id"],
                name=item["name"],
                mime_type=item.get("mimeType", ""),
                modified_time=item.get("modifiedTime"),
            )
            for item in response.get("files", [])
        ]

    def download_file(self, file_id: str, destination_path: Path) -> None:
        """Download a binary Drive file to local storage."""

        request = self._service.files().get_media(fileId=file_id, supportsAllDrives=True)
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        with destination_path.open("wb") as handle:
            downloader = self._downloader_class(handle, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()


def _matches_any(filename: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(filename, pattern) for pattern in patterns)
