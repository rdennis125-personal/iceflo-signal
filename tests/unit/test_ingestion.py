from pathlib import Path

from iceflo_signal.ingestion.csv_reader import read_sessions_csv


def test_read_sessions_csv_adds_metadata() -> None:
    frame = read_sessions_csv(Path("storage_sample/landing/incoming/sample_sessions.csv"))

    assert len(frame) == 5
    assert {"source_filename", "load_timestamp", "row_number", "source_hash"}.issubset(frame.columns)
    assert frame.loc[0, "source_filename"] == "sample_sessions.csv"
    assert frame.loc[0, "row_number"] == 2
    assert len(frame.loc[0, "source_hash"]) == 64
