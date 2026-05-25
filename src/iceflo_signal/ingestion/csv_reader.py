"""Read manual CSV exports into a raw dataframe with ingestion metadata."""

from __future__ import annotations

from datetime import datetime, timezone
from io import StringIO
from pathlib import Path

import pandas as pd

from iceflo_signal.storage import ObjectRepository
from iceflo_signal.utils.hashing import hash_record


def read_sessions_csv(path: Path) -> pd.DataFrame:
    """Read a session export and add immutable source metadata columns."""

    frame = pd.read_csv(path, dtype=str, keep_default_na=False)
    return _add_ingestion_metadata(frame, path.name)


def read_sessions_csv_from_repository(
    repository: ObjectRepository,
    key: str,
    source_filename: str | None = None,
) -> pd.DataFrame:
    """Read a session export from a storage repository."""

    content = repository.read_text(key, encoding="utf-8-sig")
    frame = pd.read_csv(StringIO(content), dtype=str, keep_default_na=False)
    return _add_ingestion_metadata(frame, source_filename or Path(key).name)


def _add_ingestion_metadata(frame: pd.DataFrame, source_filename: str) -> pd.DataFrame:
    """Add immutable ingestion metadata columns to a raw export frame."""

    load_timestamp = datetime.now(timezone.utc).isoformat()

    frame = frame.copy()
    frame["source_filename"] = source_filename
    frame["load_timestamp"] = load_timestamp
    frame["row_number"] = range(2, len(frame) + 2)
    frame["source_hash"] = frame.apply(lambda row: hash_record(row.to_dict()), axis=1)
    return frame
