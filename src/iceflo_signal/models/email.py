"""Models for validated email template rendering contexts."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class EmailEnvelope(BaseModel):
    """Shared email/report metadata available to every email template."""

    email_title: str = "Weekly Report"
    organization_name: str = "Mindful Oregon"
    report_title: str = ""
    report_period: str = ""
    intro_text: str = ""
    content_html: str = ""
    footer_text: str = (
        "This message is intended for the recipient only. Please follow your "
        "organization's privacy and security policies when handling report data."
    )


class LabelValueItem(BaseModel):
    """Reusable label/value/note row for email metrics."""

    label: str
    value: Any
    note: str = ""


class BaseCardPayload(BaseModel):
    """Payload for the Mindful base card template."""

    metric_cards: list[LabelValueItem] = Field(default_factory=list)


class ExecSummaryPayload(BaseModel):
    """Payload for the Mindful executive summary template."""

    executive_summary: str
    kpi_grid: list[LabelValueItem] = Field(default_factory=list)
    callout_title: str = "Key Takeaway"
    callout_text: str = ""


class ClinicianDigestPayload(BaseModel):
    """Payload for the Mindful clinician digest template."""

    clinician_name: str
    greeting: str = "Hello"
    summary_title: str = "Your weekly snapshot"
    snapshot_items: list[LabelValueItem] = Field(default_factory=list)


class AlertReviewPayload(BaseModel):
    """Payload for the Mindful alert review template."""

    alert_category: str = "Review Needed"
    alert_title: str
    alert_message: str
    table_columns: list[str] = Field(default_factory=list)
    table_rows: list[list[Any]] = Field(default_factory=list)


class IncompleteNoteRow(BaseModel):
    """One privacy-safe row for incomplete note notification emails."""

    date_of_service: str
    client_display_name: str
    progress_note_status: str


class IncompleteNoteNotificationPayload(BaseModel):
    """Payload for the Mindful incomplete note notification template."""

    clinician_name: str
    recipient: str
    incomplete_note_count: int
    rows: list[IncompleteNoteRow] = Field(default_factory=list)
