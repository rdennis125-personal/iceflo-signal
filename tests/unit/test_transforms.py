from pathlib import Path

from iceflo_signal.ingestion.csv_reader import read_sessions_csv
from iceflo_signal.transforms.documentation import build_clinician_documentation_status
from iceflo_signal.transforms.sessions import (
    build_dim_clinician,
    build_fact_documentation_status,
    normalize_sessions,
)


def test_transforms_build_expected_outputs() -> None:
    raw = read_sessions_csv(Path("storage_sample/landing/incoming/sample_sessions.csv"))
    normalized = normalize_sessions(raw)

    clinicians = build_dim_clinician(normalized)
    documentation = build_fact_documentation_status(normalized)
    curated = build_clinician_documentation_status(normalized)

    assert len(clinicians) == 3
    assert documentation["is_documentation_complete"].tolist().count(False) == 3
    assert curated["incomplete_session_count"].sum() == 3
    assert "SYN-1002" in curated.loc[curated["clinician_id"] == "CLN-001", "session_ids"].iloc[0]
