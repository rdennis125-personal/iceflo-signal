"""Pydantic models for source and reporting records."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

DocumentationStatus = Literal["complete", "incomplete", "missing", "late"]


class ProcessingMetadata(BaseModel):
    """Metadata retained with rows as they move through the pipeline."""

    source_filename: str
    load_timestamp: datetime
    row_number: int
    source_hash: str


class SessionRecord(BaseModel):
    """Validated source-shaped session record."""

    model_config = ConfigDict(str_strip_whitespace=True)

    session_id: str
    clinician_id: str
    clinician_name: str
    clinician_email: str
    session_date: date
    location_code: str
    program_code: str
    documentation_status: DocumentationStatus
    signed_date: date | None = None
    metadata: ProcessingMetadata


class Clinician(BaseModel):
    """Clinician dimension model."""

    clinician_id: str
    clinician_name: str
    clinician_email: str


class ValidationIssue(BaseModel):
    """Single validation issue found in a source file."""

    severity: Literal["error", "warning"] = "error"
    message: str
    row_number: int | None = None
    column: str | None = None


class ValidationResult(BaseModel):
    """Collection of validation issues."""

    issues: list[ValidationIssue] = Field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not any(issue.severity == "error" for issue in self.issues)
