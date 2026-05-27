from pathlib import Path

import pytest

from iceflo_signal.storage import GoogleDriveObjectRepository, LocalFileRepository
from iceflo_signal.storage.gcs_repository import _parse_root_ref


class FakeGoogleDriveObjectClient:
    def __init__(self) -> None:
        self.objects: dict[str, tuple[bytes, str]] = {}

    def exists(self, key: str) -> bool:
        return key in self.objects

    def read_bytes(self, key: str) -> bytes:
        return self.objects[key][0]

    def write_bytes(self, key: str, content: bytes, content_type: str) -> None:
        self.objects[key] = (content, content_type)


def test_local_file_repository_reads_and_writes_text(tmp_path: Path) -> None:
    repository = LocalFileRepository(tmp_path)

    repository.write_text("landing/example.csv", "hello", content_type="text/csv")

    assert repository.exists("landing/example.csv")
    assert repository.read_text("landing/example.csv") == "hello"
    assert (tmp_path / "landing" / "example.csv").exists()


def test_local_file_repository_rejects_escaping_keys(tmp_path: Path) -> None:
    repository = LocalFileRepository(tmp_path)

    with pytest.raises(ValueError, match="Invalid storage key"):
        repository.write_text("../outside.csv", "nope")


def test_google_drive_object_repository_uses_same_contract() -> None:
    client = FakeGoogleDriveObjectClient()
    repository = GoogleDriveObjectRepository(client)

    repository.write_text("curated/demo.html", "<p>Hello</p>", content_type="text/html")

    assert repository.exists("curated/demo.html")
    assert repository.read_text("curated/demo.html") == "<p>Hello</p>"
    assert client.objects["curated/demo.html"][1] == "text/html"


def test_google_drive_object_repository_rejects_invalid_keys() -> None:
    repository = GoogleDriveObjectRepository(FakeGoogleDriveObjectClient())

    with pytest.raises(ValueError, match="Invalid Drive object key"):
        repository.read_text("/absolute/path.csv")


def test_gcs_root_reference_parses_bucket_and_optional_prefix() -> None:
    assert _parse_root_ref("iceflo-signal-dev-1") == ("iceflo-signal-dev-1", "")
    assert _parse_root_ref("gs://mindful-oregon-data-root/test") == ("mindful-oregon-data-root", "test")
