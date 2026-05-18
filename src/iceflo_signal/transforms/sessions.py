"""Session normalization, fact, and dimension builders."""

from __future__ import annotations

import pandas as pd


def normalize_sessions(raw: pd.DataFrame) -> pd.DataFrame:
    """Standardize source values into a normalized sessions dataframe."""

    frame = raw.copy()
    frame["session_id"] = frame["session_id"].str.strip()
    frame["clinician_id"] = frame["clinician_id"].str.strip().str.upper()
    frame["clinician_name"] = frame["clinician_name"].str.strip()
    frame["clinician_email"] = frame["clinician_email"].str.strip().str.lower()
    frame["location_code"] = frame["location_code"].str.strip().str.upper()
    frame["program_code"] = frame["program_code"].str.strip().str.upper()
    frame["documentation_status"] = frame["documentation_status"].str.strip().str.lower()
    frame["session_date"] = pd.to_datetime(frame["session_date"]).dt.date
    frame["signed_date"] = pd.to_datetime(frame["signed_date"].replace("", pd.NA), errors="coerce").dt.date
    frame["is_documentation_complete"] = frame["documentation_status"].eq("complete")
    frame["documentation_age_days"] = (
        pd.Timestamp.utcnow().normalize().date() - pd.to_datetime(frame["session_date"]).dt.date
    ).apply(lambda value: value.days)
    return frame


def build_dim_clinician(normalized: pd.DataFrame) -> pd.DataFrame:
    """Build the clinician dimension from normalized sessions."""

    return (
        normalized[["clinician_id", "clinician_name", "clinician_email"]]
        .drop_duplicates()
        .sort_values("clinician_id")
        .reset_index(drop=True)
    )


def build_dim_date(normalized: pd.DataFrame) -> pd.DataFrame:
    """Build a small date dimension for observed session dates."""

    dates = pd.DataFrame({"date": sorted(normalized["session_date"].unique())})
    as_datetime = pd.to_datetime(dates["date"])
    dates["date_key"] = as_datetime.dt.strftime("%Y%m%d")
    dates["year"] = as_datetime.dt.year
    dates["month"] = as_datetime.dt.month
    dates["week"] = as_datetime.dt.isocalendar().week.astype(int)
    dates["day_of_week"] = as_datetime.dt.day_name()
    return dates[["date_key", "date", "year", "month", "week", "day_of_week"]]


def build_fact_session(normalized: pd.DataFrame) -> pd.DataFrame:
    """Build a session-level fact table."""

    columns = [
        "session_id",
        "clinician_id",
        "session_date",
        "location_code",
        "program_code",
        "source_filename",
        "load_timestamp",
        "row_number",
        "source_hash",
    ]
    return normalized[columns].copy()


def build_fact_documentation_status(normalized: pd.DataFrame) -> pd.DataFrame:
    """Build a documentation-status fact table."""

    columns = [
        "session_id",
        "clinician_id",
        "session_date",
        "documentation_status",
        "signed_date",
        "is_documentation_complete",
        "documentation_age_days",
        "source_filename",
        "load_timestamp",
        "row_number",
        "source_hash",
    ]
    return normalized[columns].copy()
