"""Read manual CSV exports into a raw dataframe with ingestion metadata."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from iceflo_signal.utils.hashing import hash_record


def read_sessions_csv(path: Path) -> pd.DataFrame:
    """Read a session export and add immutable source metadata columns."""

    frame = pd.read_csv(path, dtype=str, keep_default_na=False)
    load_timestamp = datetime.now(timezone.utc).isoformat()

    frame = frame.copy()
    frame["source_filename"] = path.name
    frame["load_timestamp"] = load_timestamp
    frame["row_number"] = range(2, len(frame) + 2)
    frame["source_hash"] = frame.apply(lambda row: hash_record(row.to_dict()), axis=1)
    return frame
