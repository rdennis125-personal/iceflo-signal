"""Validation rules for session CSV exports."""

from __future__ import annotations

import pandas as pd

from iceflo_signal.models.session import ValidationIssue, ValidationResult

REQUIRED_COLUMNS = {
    "session_id",
    "clinician_id",
    "clinician_name",
    "clinician_email",
    "session_date",
    "location_code",
    "program_code",
    "documentation_status",
}

ALLOWED_DOCUMENTATION_STATUSES = {"complete", "incomplete", "missing", "late"}
REQUIRED_NON_NULL_COLUMNS = REQUIRED_COLUMNS


def validate_session_export(frame: pd.DataFrame) -> ValidationResult:
    """Validate required columns, dates, null rules, and status values."""

    issues: list[ValidationIssue] = []
    missing_columns = sorted(REQUIRED_COLUMNS.difference(frame.columns))
    for column in missing_columns:
        issues.append(ValidationIssue(message=f"Missing required column: {column}", column=column))

    if missing_columns:
        return ValidationResult(issues=issues)

    for index, row in frame.iterrows():
        row_number = int(row.get("row_number", index + 2))

        for column in REQUIRED_NON_NULL_COLUMNS:
            value = str(row.get(column, "")).strip()
            if not value:
                issues.append(
                    ValidationIssue(
                        message=f"Required value is blank: {column}",
                        row_number=row_number,
                        column=column,
                    )
                )

        status = str(row.get("documentation_status", "")).strip().lower()
        if status and status not in ALLOWED_DOCUMENTATION_STATUSES:
            issues.append(
                ValidationIssue(
                    message=f"Invalid documentation_status: {status}",
                    row_number=row_number,
                    column="documentation_status",
                )
            )

        for column in ("session_date", "signed_date"):
            value = str(row.get(column, "")).strip()
            if value and pd.isna(pd.to_datetime(value, errors="coerce")):
                issues.append(
                    ValidationIssue(
                        message=f"Invalid date value: {column}",
                        row_number=row_number,
                        column=column,
                    )
                )

    return ValidationResult(issues=issues)
