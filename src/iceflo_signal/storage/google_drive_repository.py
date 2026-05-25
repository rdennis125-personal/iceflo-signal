"""Google Drive implementation of the object repository contract."""

from __future__ import annotations

from io import BytesIO
from pathlib import PurePosixPath
from typing import Protocol


class GoogleDriveObjectClient(Protocol):
    """Drive operations needed by the repository adapter."""

    def exists(self, key: str) -> bool:
        """Return true when a Drive object exists at key."""

    def read_bytes(self, key: str) -> bytes:
        """Read a Drive object as bytes."""

    def write_bytes(self, key: str, content: bytes, content_type: str) -> None:
        """Write bytes to a Drive object key."""


class GoogleDriveObjectRepository:
    """Object repository backed by a Google Drive folder tree."""

    def __init__(self, client: GoogleDriveObjectClient) -> None:
        self._client = client

    def exists(self, key: str) -> bool:
        return self._client.exists(_normalize_key(key))

    def read_bytes(self, key: str) -> bytes:
        return self._client.read_bytes(_normalize_key(key))

    def write_bytes(self, key: str, content: bytes, content_type: str = "application/octet-stream") -> None:
        self._client.write_bytes(_normalize_key(key), content, content_type)

    def read_text(self, key: str, encoding: str = "utf-8") -> str:
        return self.read_bytes(key).decode(encoding)

    def write_text(self, key: str, content: str, encoding: str = "utf-8", content_type: str = "text/plain") -> None:
        self.write_bytes(key, content.encode(encoding), content_type)


class GoogleApiDriveObjectClient:
    """Google Drive object client backed by google-api-python-client."""

    folder_mime_type = "application/vnd.google-apps.folder"

    def __init__(self, credentials: object, root_folder_id: str) -> None:
        try:
            from googleapiclient.discovery import build
            from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
        except ImportError as exc:
            raise RuntimeError(
                "Google Drive repository requires google-api-python-client. "
                "Install project requirements before using Drive-backed storage."
            ) from exc

        self._service = build("drive", "v3", credentials=credentials)
        self._download_class = MediaIoBaseDownload
        self._upload_class = MediaIoBaseUpload
        self._root_folder_id = root_folder_id

    def exists(self, key: str) -> bool:
        return self._file_id_for_key(key) is not None

    def read_bytes(self, key: str) -> bytes:
        file_id = self._file_id_for_key(key)
        if not file_id:
            raise FileNotFoundError(key)

        request = self._service.files().get_media(fileId=file_id, supportsAllDrives=True)
        handle = BytesIO()
        downloader = self._download_class(handle, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        return handle.getvalue()

    def write_bytes(self, key: str, content: bytes, content_type: str) -> None:
        parts = PurePosixPath(key).parts
        if not parts:
            raise ValueError("Drive object key cannot be empty.")

        parent_id = self._ensure_parent_folder(parts[:-1])
        filename = parts[-1]
        media = self._upload_class(BytesIO(content), mimetype=content_type, resumable=False)
        existing_file_id = self._find_child(parent_id, filename)

        if existing_file_id:
            self._service.files().update(
                fileId=existing_file_id,
                media_body=media,
                supportsAllDrives=True,
            ).execute()
            return

        metadata = {"name": filename, "parents": [parent_id]}
        self._service.files().create(
            body=metadata,
            media_body=media,
            fields="id",
            supportsAllDrives=True,
        ).execute()

    def _file_id_for_key(self, key: str) -> str | None:
        parts = PurePosixPath(key).parts
        if not parts:
            return None

        parent_id = self._root_folder_id
        for folder_name in parts[:-1]:
            folder_id = self._find_child(parent_id, folder_name, mime_type=self.folder_mime_type)
            if not folder_id:
                return None
            parent_id = folder_id
        return self._find_child(parent_id, parts[-1])

    def _ensure_parent_folder(self, folder_parts: tuple[str, ...]) -> str:
        parent_id = self._root_folder_id
        for folder_name in folder_parts:
            folder_id = self._find_child(parent_id, folder_name, mime_type=self.folder_mime_type)
            if folder_id:
                parent_id = folder_id
                continue

            metadata = {
                "name": folder_name,
                "parents": [parent_id],
                "mimeType": self.folder_mime_type,
            }
            created = self._service.files().create(
                body=metadata,
                fields="id",
                supportsAllDrives=True,
            ).execute()
            parent_id = created["id"]
        return parent_id

    def _find_child(self, parent_id: str, name: str, mime_type: str | None = None) -> str | None:
        escaped_name = name.replace("\\", "\\\\").replace("'", "\\'")
        query = f"'{parent_id}' in parents and name = '{escaped_name}' and trashed = false"
        if mime_type:
            query += f" and mimeType = '{mime_type}'"

        response = (
            self._service.files()
            .list(
                q=query,
                fields="files(id)",
                pageSize=1,
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
            )
            .execute()
        )
        files = response.get("files", [])
        return files[0]["id"] if files else None


def _normalize_key(key: str) -> str:
    normalized = PurePosixPath(str(key).replace("\\", "/"))
    if normalized.is_absolute() or ".." in normalized.parts or not normalized.parts:
        raise ValueError(f"Invalid Drive object key: {key}")
    return normalized.as_posix()
