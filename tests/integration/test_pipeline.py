from pathlib import Path

from iceflo_signal.pipeline import run_local_pipeline


def test_run_local_pipeline_writes_outputs(tmp_path: Path) -> None:
    result = run_local_pipeline(
        Path("storage_sample/landing/incoming/sample_sessions.csv"),
        tmp_path,
        Path("templates"),
    )

    assert result.rows_processed == 5
    assert (tmp_path / "normalized" / "sessions_normalized.csv").exists()
    assert (tmp_path / "facts" / "fact_session.csv").exists()
    assert (tmp_path / "curated" / "curated_clinician_documentation_status.csv").exists()
    assert (tmp_path / "curated" / "notifications" / "cln-001_documentation_followup.html").exists()
