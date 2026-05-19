"""Generate local demo previews for registered email templates."""

from __future__ import annotations

from dataclasses import dataclass
from email.message import EmailMessage
from pathlib import Path
from typing import Any

from iceflo_signal.delivery.template_factory import DEFAULT_TEMPLATE_REGISTRY, EmailTemplateFactory
from iceflo_signal.models.email import (
    AlertReviewPayload,
    BaseCardPayload,
    ClinicianDigestPayload,
    EmailEnvelope,
    ExecSummaryPayload,
    IncompleteNoteNotificationPayload,
    IncompleteNoteRow,
    LabelValueItem,
)


@dataclass(frozen=True)
class DemoRenderResult:
    """Output paths from a template demo render."""

    html_paths: list[Path]
    eml_paths: list[Path]
    index_path: Path


def render_template_demos(
    recipient: str,
    output_dir: Path,
    template_dir: Path = Path("templates"),
    sender: str = "no-reply@iceflo-signal.example",
) -> DemoRenderResult:
    """Render hello-world/lorem-ipsum demos for every registered template."""

    output_dir.mkdir(parents=True, exist_ok=True)
    factory = EmailTemplateFactory(template_dir=template_dir)

    html_paths: list[Path] = []
    eml_paths: list[Path] = []
    for template_id in sorted(DEFAULT_TEMPLATE_REGISTRY):
        envelope, payload = _demo_context_for(template_id, recipient)
        html = factory.render(template_id, envelope, payload)
        slug = template_id.replace(".", "_")

        html_path = output_dir / f"{slug}.html"
        html_path.write_text(html, encoding="utf-8")
        html_paths.append(html_path)

        eml_path = output_dir / f"{slug}.eml"
        eml_path.write_text(
            _build_eml(
                recipient=recipient,
                sender=sender,
                subject=envelope.email_title,
                html=html,
            ),
            encoding="utf-8",
        )
        eml_paths.append(eml_path)

    index_path = output_dir / "index.html"
    index_path.write_text(_build_index(html_paths, eml_paths, recipient), encoding="utf-8")
    return DemoRenderResult(html_paths=html_paths, eml_paths=eml_paths, index_path=index_path)


def _demo_context_for(template_id: str, recipient: str) -> tuple[EmailEnvelope, Any]:
    envelope = EmailEnvelope(
        email_title=f"ICEFLO Signal Demo - {template_id}",
        organization_name="Mindful Oregon",
        report_title="Hello World Reporting Demo",
        report_period="Demo period: May 4-10, 2026",
        intro_text=(
            "Hello world. Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
            f"This preview is parameterized for {recipient}."
        ),
        content_html=(
            "<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
            "Integer posuere erat a ante venenatis dapibus posuere velit aliquet.</p>"
        ),
        footer_text=(
            "Demo only. Do not use for PHI, credentials, production exports, "
            "or real client data."
        ),
    )

    payload_by_template = {
        "mindful_oregon.alert_review": AlertReviewPayload(
            alert_title="Hello world alert",
            alert_message="Lorem ipsum review item generated for template QA.",
            table_columns=["Item", "Status", "Owner"],
            table_rows=[
                ["SYN-DEMO-001", "Review Needed", recipient],
                ["SYN-DEMO-002", "Pending", "Demo Team"],
            ],
        ),
        "mindful_oregon.base_card": BaseCardPayload(
            metric_cards=[
                LabelValueItem(label="Hello", value="1", note="Demo metric"),
                LabelValueItem(label="World", value="2", note="Lorem ipsum"),
                LabelValueItem(label="Ready", value="100%", note="Preview only"),
            ]
        ),
        "mindful_oregon.clinician_digest": ClinicianDigestPayload(
            clinician_name="Demo Recipient",
            snapshot_items=[
                LabelValueItem(label="Open items", value=3),
                LabelValueItem(label="Completed", value=12),
                LabelValueItem(label="Recipient", value=recipient),
            ],
        ),
        "mindful_oregon.exec_summary": ExecSummaryPayload(
            executive_summary=(
                "Hello world executive summary. Lorem ipsum dolor sit amet, "
                "consectetur adipiscing elit."
            ),
            kpi_grid=[
                LabelValueItem(label="Completion rate", value="92%", note="Demo value"),
                LabelValueItem(label="Review queue", value=3, note="Synthetic only"),
                LabelValueItem(label="Recipient", value=recipient, note="Parameterized"),
            ],
            callout_text="This template preview uses synthetic lorem ipsum context.",
        ),
        "mindful_oregon.incomplete_note_notification": IncompleteNoteNotificationPayload(
            clinician_name="Demo Clinician",
            recipient=recipient,
            incomplete_note_count=2,
            rows=[
                IncompleteNoteRow(
                    date_of_service="05/02/2026 2:30 PM",
                    client_display_name="Jo Jo",
                    progress_note_status="NO NOTE",
                ),
                IncompleteNoteRow(
                    date_of_service="05/03/2026 9:00 AM",
                    client_display_name="Av St",
                    progress_note_status="DRAFT",
                ),
            ],
        ),
    }
    return envelope, payload_by_template[template_id]


def _build_eml(recipient: str, sender: str, subject: str, html: str) -> str:
    message = EmailMessage()
    message["To"] = recipient
    message["From"] = sender
    message["Subject"] = subject
    message.set_content("This email requires an HTML-capable email client.")
    message.add_alternative(html, subtype="html")
    return message.as_string()


def _build_index(html_paths: list[Path], eml_paths: list[Path], recipient: str) -> str:
    rows = "\n".join(
        f"<li><a href=\"{html_path.name}\">{html_path.stem}</a> "
        f"(<a href=\"{eml_path.name}\">email draft</a>)</li>"
        for html_path, eml_path in zip(html_paths, eml_paths, strict=True)
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>ICEFLO Signal Template Demos</title>
</head>
<body>
  <h1>ICEFLO Signal Template Demos</h1>
  <p>Recipient: {recipient}</p>
  <ul>
    {rows}
  </ul>
</body>
</html>
"""
