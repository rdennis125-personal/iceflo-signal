"""Stable hashing helpers for source records."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def hash_record(record: dict[str, Any]) -> str:
    """Return a stable SHA-256 hash for a source record."""

    payload = {
        key: value
        for key, value in record.items()
        if key not in {"source_filename", "load_timestamp", "row_number", "source_hash"}
    }
    encoded = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
