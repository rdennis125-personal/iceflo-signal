"""Google Cloud Storage implementation of the object repository contract."""

from __future__ import annotations

from pathlib import PurePosixPath


class GcsObjectRepository:
    """Object repository backed by a Google Cloud Storage bucket or prefix."""

    def __init__(self, bucket_name: str, prefix: str = "") -> None:
        try:
            from google.cloud import storage
        except ImportError as exc:
            raise RuntimeError(
                "GCS repository requires google-cloud-storage. "
                "Install project requirements before using GCS-backed storage."
            ) from exc

        self._client = storage.Client()
        self._bucket = self._client.bucket(bucket_name)
        self._prefix = _normalize_prefix(prefix)

    @classmethod
    def from_root_ref(cls, root_ref: str) -> "GcsObjectRepository":
        """Build a repository from a bucket name or gs://bucket/optional-prefix URI."""

        bucket_name, prefix = _parse_root_ref(root_ref)
        return cls(bucket_name=bucket_name, prefix=prefix)

    def exists(self, key: str) -> bool:
        return self._bucket.blob(self._blob_name(key)).exists()

    def read_bytes(self, key: str) -> bytes:
        return self._bucket.blob(self._blob_name(key)).download_as_bytes()

    def write_bytes(self, key: str, content: bytes, content_type: str = "application/octet-stream") -> None:
        self._bucket.blob(self._blob_name(key)).upload_from_string(content, content_type=content_type)

    def read_text(self, key: str, encoding: str = "utf-8") -> str:
        return self.read_bytes(key).decode(encoding)

    def write_text(self, key: str, content: str, encoding: str = "utf-8", content_type: str = "text/plain") -> None:
        self.write_bytes(key, content.encode(encoding), content_type)

    def _blob_name(self, key: str) -> str:
        normalized = _normalize_key(key)
        if not self._prefix:
            return normalized
        return f"{self._prefix}/{normalized}"


def _parse_root_ref(root_ref: str) -> tuple[str, str]:
    value = root_ref.strip()
    if not value:
        raise ValueError("GCS root reference cannot be empty.")

    if value.startswith("gs://"):
        path = value.removeprefix("gs://")
        bucket_name, _, prefix = path.partition("/")
        if not bucket_name:
            raise ValueError(f"Invalid GCS root reference: {root_ref}")
        return bucket_name, prefix

    bucket_name, _, prefix = value.partition("/")
    return bucket_name, prefix


def _normalize_key(key: str) -> str:
    normalized = PurePosixPath(str(key).replace("\\", "/"))
    if normalized.is_absolute() or ".." in normalized.parts or not normalized.parts:
        raise ValueError(f"Invalid GCS object key: {key}")
    return normalized.as_posix()


def _normalize_prefix(prefix: str) -> str:
    if not prefix:
        return ""
    return _normalize_key(prefix).rstrip("/")
