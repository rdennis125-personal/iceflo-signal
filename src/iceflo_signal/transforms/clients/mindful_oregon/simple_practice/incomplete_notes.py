"""Curate appointment rows into clinician incomplete-note digests."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable


@dataclass(frozen=True)
class IncompleteNoteRecord:
    """One appointment whose progress note still needs attention."""

    clinician_name: str
    date_of_service: str
    client_display_name: str
    client_key: str
    progress_note_status: str


@dataclass(frozen=True)
class IncompleteNoteDigest:
    """Clinician-specific collection of incomplete note records."""

    clinician_name: str
    records: tuple[IncompleteNoteRecord, ...]


class IncompleteNoteTransformer:
    """Build clinician digests for appointments with unlocked progress notes."""

    complete_status = "LOCKED"

    def build_records(self, appointment_rows: Iterable[dict[str, object]]) -> list[IncompleteNoteRecord]:
        """Filter appointment rows to Progress Note Status values other than LOCKED."""

        records: list[IncompleteNoteRecord] = []
        for row in appointment_rows:
            status = str(row.get("Progress Note Status", "")).strip()
            if not status or status.upper() == self.complete_status:
                continue

            records.append(
                IncompleteNoteRecord(
                    clinician_name=str(row.get("Clinician", "")).strip(),
                    date_of_service=_format_date_of_service(str(row.get("Date of Service", "")).strip()),
                    client_display_name=str(row.get("client_display_name", "")).strip(),
                    client_key=str(row.get("client_key", "")).strip(),
                    progress_note_status=status,
                )
            )

        return sorted(records, key=lambda record: (record.clinician_name, record.date_of_service, record.client_key))

    def build_digests(self, appointment_rows: Iterable[dict[str, object]]) -> list[IncompleteNoteDigest]:
        """Group incomplete-note records by clinician."""

        grouped: dict[str, list[IncompleteNoteRecord]] = defaultdict(list)
        for record in self.build_records(appointment_rows):
            grouped[record.clinician_name].append(record)

        return [
            IncompleteNoteDigest(clinician_name=clinician_name, records=tuple(records))
            for clinician_name, records in sorted(grouped.items())
        ]


def _format_date_of_service(value: str) -> str:
    for date_format in ("%m/%d/%Y %H:%M", "%m/%d/%Y %I:%M %p", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            parsed = datetime.strptime(value, date_format)
            return parsed.strftime("%m/%d/%Y %I:%M %p").replace(" 0", " ")
        except ValueError:
            continue
    return value
