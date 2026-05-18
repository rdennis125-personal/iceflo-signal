"""Curated documentation reporting datasets."""

from __future__ import annotations

import pandas as pd


def build_clinician_documentation_status(normalized: pd.DataFrame) -> pd.DataFrame:
    """Create clinician-level documentation follow-up rows.

    The curated output contains already-calculated metrics so templates can stay
    focused on presentation instead of business logic.
    """

    incomplete = normalized[~normalized["is_documentation_complete"]].copy()
    if incomplete.empty:
        return pd.DataFrame(
            columns=[
                "clinician_id",
                "clinician_name",
                "clinician_email",
                "incomplete_session_count",
                "oldest_session_date",
                "latest_session_date",
                "max_documentation_age_days",
                "session_ids",
            ]
        )

    grouped = (
        incomplete.groupby(["clinician_id", "clinician_name", "clinician_email"], as_index=False)
        .agg(
            incomplete_session_count=("session_id", "count"),
            oldest_session_date=("session_date", "min"),
            latest_session_date=("session_date", "max"),
            max_documentation_age_days=("documentation_age_days", "max"),
            session_ids=("session_id", lambda values: ", ".join(sorted(values))),
        )
        .sort_values(["clinician_name", "clinician_id"])
        .reset_index(drop=True)
    )
    return grouped
