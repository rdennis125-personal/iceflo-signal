import pandas as pd

from iceflo_signal.validation.sessions import validate_session_export


def test_validation_rejects_missing_required_columns() -> None:
    result = validate_session_export(pd.DataFrame({"session_id": ["SYN-1"]}))

    assert not result.is_valid
    assert any("Missing required column" in issue.message for issue in result.issues)


def test_validation_rejects_invalid_status() -> None:
    frame = pd.DataFrame(
        [
            {
                "session_id": "SYN-1",
                "clinician_id": "CLN-1",
                "clinician_name": "Synthetic Clinician",
                "clinician_email": "synthetic@example.test",
                "session_date": "2026-05-01",
                "location_code": "WEST",
                "program_code": "ADULT",
                "documentation_status": "unknown",
                "row_number": 2,
            }
        ]
    )

    result = validate_session_export(frame)

    assert not result.is_valid
    assert result.issues[0].column == "documentation_status"
