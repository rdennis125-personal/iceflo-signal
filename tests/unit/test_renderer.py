from pathlib import Path

from iceflo_signal.delivery.renderer import render_clinician_followups
from iceflo_signal.ingestion.csv_reader import read_sessions_csv
from iceflo_signal.transforms.documentation import build_clinician_documentation_status
from iceflo_signal.transforms.sessions import normalize_sessions


def test_render_clinician_followups(tmp_path: Path) -> None:
    raw = read_sessions_csv(Path("storage_sample/landing/incoming/sample_sessions.csv"))
    curated = build_clinician_documentation_status(normalize_sessions(raw))

    paths = render_clinician_followups(curated, Path("templates"), tmp_path)

    assert len(paths) == 3
    assert paths[0].exists()
    assert "Documentation Follow-up" in paths[0].read_text(encoding="utf-8")
