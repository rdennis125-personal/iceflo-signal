"""Repository interfaces for object-like storage backends."""

from __future__ import annotations

from pathlib import Path, PurePosixPath
from typing import Protocol


class ObjectRepository(Protocol):
    """Storage boundary for reading and writing named objects."""

    def exists(self, key: str) -> bool:
        """Return true when an object exists."""

    def read_bytes(self, key: str) -> bytes:
        """Read an object as bytes."""

    def write_bytes(self, key: str, content: bytes, content_type: str = "application/octet-stream") -> None:
        """Write bytes to an object."""

    def read_text(self, key: str, encoding: str = "utf-8") -> str:
        """Read an object as text."""

    def write_text(self, key: str, content: str, encoding: str = "utf-8", content_type: str = "text/plain") -> None:
        """Write text to an object."""


class LocalFileRepository:
    """Object repository backed by a local filesystem root."""

    def __init__(self, root: Path = Path(".")) -> None:
        self._root = root.resolve()

    def exists(self, key: str) -> bool:
        return self._resolve(key).exists()

    def read_bytes(self, key: str) -> bytes:
        return self._resolve(key).read_bytes()

    def write_bytes(self, key: str, content: bytes, content_type: str = "application/octet-stream") -> None:
        path = self._resolve(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    def read_text(self, key: str, encoding: str = "utf-8") -> str:
        return self._resolve(key).read_text(encoding=encoding)

    def write_text(self, key: str, content: str, encoding: str = "utf-8", content_type: str = "text/plain") -> None:
        path = self._resolve(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding=encoding)

    def path_for(self, key: str) -> Path:
        """Return a local path for integrations that still need filesystem access."""

        return self._resolve(key)

    def _resolve(self, key: str) -> Path:
        normalized = _normalize_key(key)
        path = (self._root / normalized).resolve()
        if not path.is_relative_to(self._root):
            raise ValueError(f"Storage key escapes repository root: {key}")
        return path


def _normalize_key(key: str) -> PurePosixPath:
    normalized = PurePosixPath(str(key).replace("\\", "/"))
    if normalized.is_absolute() or ".." in normalized.parts:
        raise ValueError(f"Invalid storage key: {key}")
    return normalized
