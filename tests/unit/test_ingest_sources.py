from pathlib import Path

import pytest

from iceflo_signal.config import GoogleDriveSourceConfig, load_client_ingest_config
from iceflo_signal.ingestion.google_drive import DriveFile, GoogleDriveIngestSource


class FakeDriveClient:
    def __init__(self) -> None:
        self.folder_ids: list[str] = []
        self.downloads: list[tuple[str, Path]] = []

    def list_files(self, folder_id: str) -> list[DriveFile]:
        self.folder_ids.append(folder_id)
        return [
            DriveFile(file_id="csv-1", name="appointment-status-report.csv", mime_type="text/csv"),
            DriveFile(file_id="doc-1", name="notes.txt", mime_type="text/plain"),
            DriveFile(file_id="csv-2", name="client_details_report.csv", mime_type="text/csv"),
        ]

    def download_file(self, file_id: str, destination_path: Path) -> None:
        self.downloads.append((file_id, destination_path))
        destination_path.write_text(f"downloaded {file_id}", encoding="utf-8")


def test_load_client_ingest_config_reads_google_drive_source() -> None:
    config = load_client_ingest_config(Path("config/clients/mindful_oregon/ingest_sources.json"))
    source = config.get_source("mindful_oregon_simple_practice_drive")

    assert config.client_key == "mindful_oregon"
    assert source.source_type == "google_drive"
    assert source.auth_mode == "user_oauth"
    assert source.folder_id_env == "ICEFLO_MINDFUL_OREGON_DRIVE_FOLDER_ID"
    assert source.destination_path == Path("storage_sample/landing/clients/mindful_oregon/simple_practice/incoming")


def test_google_drive_ingest_source_downloads_matching_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ICEFLO_TEST_DRIVE_FOLDER_ID", "folder-123")
    config = GoogleDriveSourceConfig(
        source_id="test_drive_source",
        client_key="mindful_oregon",
        system_key="simple_practice",
        folder_id_env="ICEFLO_TEST_DRIVE_FOLDER_ID",
        destination_path=tmp_path,
        file_name_patterns=["*.csv"],
    )
    fake_client = FakeDriveClient()

    downloaded = GoogleDriveIngestSource(config=config, drive_client=fake_client).sync()

    assert fake_client.folder_ids == ["folder-123"]
    assert [item.drive_file.name for item in downloaded] == [
        "appointment-status-report.csv",
        "client_details_report.csv",
    ]
    assert fake_client.downloads == [
        ("csv-1", tmp_path / "appointment-status-report.csv"),
        ("csv-2", tmp_path / "client_details_report.csv"),
    ]
    assert (tmp_path / "appointment-status-report.csv").read_text(encoding="utf-8") == "downloaded csv-1"


def test_google_drive_source_requires_folder_id_environment_variable(tmp_path: Path) -> None:
    config = GoogleDriveSourceConfig(
        source_id="test_drive_source",
        client_key="mindful_oregon",
        system_key="simple_practice",
        folder_id_env="ICEFLO_MISSING_FOLDER_ID",
        destination_path=tmp_path,
    )

    with pytest.raises(RuntimeError, match="ICEFLO_MISSING_FOLDER_ID"):
        GoogleDriveIngestSource(config=config, drive_client=FakeDriveClient()).sync()
