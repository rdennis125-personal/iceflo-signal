"""Base classes for Mindful Oregon SimplePractice CSV exports."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
from typing import Iterable

from iceflo_signal.privacy import ClientIdentityTransformer
from iceflo_signal.storage import ObjectRepository
from iceflo_signal.utils.hashing import hash_record


@dataclass(frozen=True)
class SimplePracticeExportDefinition:
    """Schema and privacy metadata for one SimplePractice CSV export."""

    export_name: str
    expected_columns: tuple[str, ...]
    client_name_columns: tuple[str, ...] = ()


class SimplePracticeCsvProcessor:
    """Read a SimplePractice CSV and emit privacy-safe row dictionaries."""

    definition: SimplePracticeExportDefinition

    def __init__(self, client_namespace: str = "mindful_oregon") -> None:
        self._identity_transformer = ClientIdentityTransformer(
            namespace=f"{client_namespace}:simple_practice"
        )

    def process(self, path: Path) -> list[dict[str, object]]:
        """Read and transform a CSV export into privacy-safe records."""

        with path.open(newline="", encoding="utf-8-sig") as handle:
            return self.process_text(handle.read(), source_filename=path.name)

    def process_from_repository(self, repository: ObjectRepository, key: str) -> list[dict[str, object]]:
        """Read and transform a CSV export from a storage repository."""

        return self.process_text(repository.read_text(key, encoding="utf-8-sig"), source_filename=Path(key).name)

    def process_text(self, content: str, source_filename: str) -> list[dict[str, object]]:
        """Transform CSV text into privacy-safe records."""

        rows: list[dict[str, object]] = []
        load_timestamp = datetime.now(timezone.utc).isoformat()

        reader = csv.reader(StringIO(content))
        try:
            headers = next(reader)
        except StopIteration:
            return []

        normalized_headers = _deduplicate_headers(headers)
        self.validate_headers(headers)

        for row_number, values in enumerate(reader, start=2):
            source_row = dict(zip(normalized_headers, values, strict=False))
            if self.should_skip_row(source_row):
                continue
            transformed = self.transform_row(source_row)
            transformed.update(
                {
                    "source_export": self.definition.export_name,
                    "source_filename": source_filename,
                    "load_timestamp": load_timestamp,
                    "row_number": row_number,
                    "source_hash": hash_record(source_row),
                }
            )
            rows.append(transformed)

        return rows

    def validate_headers(self, headers: Iterable[str]) -> None:
        """Validate that the source CSV includes the configured columns."""

        missing = set(self.definition.expected_columns).difference(headers)
        if missing:
            missing_text = ", ".join(sorted(missing))
            raise ValueError(f"{self.definition.export_name} missing columns: {missing_text}")

    def transform_row(self, row: dict[str, str]) -> dict[str, object]:
        """Return a privacy-safe copy of a source row."""

        transformed: dict[str, object] = dict(row)

        for column in self.definition.client_name_columns:
            source_name = str(row.get(column, "")).strip()
            identity = self._identity_transformer.transform_name(source_name)
            transformed.pop(column, None)
            transformed[f"{_snake_case(column)}_display_name"] = identity.client_display_name
            transformed[f"{_snake_case(column)}_key"] = identity.client_key

        return transformed

    def should_skip_row(self, row: dict[str, str]) -> bool:
        """Return true when an export-specific processor should skip a row."""

        return False


def _deduplicate_headers(headers: Iterable[str]) -> list[str]:
    seen: dict[str, int] = {}
    deduplicated: list[str] = []
    for header in headers:
        count = seen.get(header, 0) + 1
        seen[header] = count
        deduplicated.append(header if count == 1 else f"{header}__{count}")
    return deduplicated


def _snake_case(value: str) -> str:
    return (
        value.strip()
        .replace(".", "")
        .replace("-", " ")
        .replace("/", " ")
        .lower()
        .replace(" ", "_")
    )
