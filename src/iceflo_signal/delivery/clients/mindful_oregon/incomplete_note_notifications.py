"""Render clinician incomplete-note notification drafts."""

from __future__ import annotations

import re
from dataclasses import dataclass
from email.message import EmailMessage
from pathlib import Path

from iceflo_signal.delivery.template_factory import EmailTemplateFactory
from iceflo_signal.models.email import EmailEnvelope, IncompleteNoteNotificationPayload, IncompleteNoteRow
from iceflo_signal.transforms.clients.mindful_oregon.simple_practice import IncompleteNoteDigest


@dataclass(frozen=True)
class NotificationRenderResult:
    """Output paths from rendering incomplete-note notifications."""

    html_paths: list[Path]
    eml_paths: list[Path]
    index_path: Path


class IncompleteNoteNotificationRenderer:
    """Render one dry-run notification per clinician digest."""

    def __init__(
        self,
        template_dir: Path = Path("templates"),
        sender: str = "no-reply@iceflo-signal.example",
    ) -> None:
        self._factory = EmailTemplateFactory(template_dir=template_dir)
        self._sender = sender

    def render(
        self,
        digests: list[IncompleteNoteDigest],
        output_dir: Path,
        recipient: str,
        report_period: str,
    ) -> NotificationRenderResult:
        """Write HTML previews and .eml drafts for clinician incomplete-note digests."""

        output_dir.mkdir(parents=True, exist_ok=True)
        html_paths: list[Path] = []
        eml_paths: list[Path] = []

        for digest in digests:
            subject = f"Incomplete progress notes - {digest.clinician_name}"
            envelope = EmailEnvelope(
                email_title=subject,
                organization_name="Mindful Oregon",
                report_title="Incomplete Progress Notes",
                report_period=report_period,
            )
            payload = IncompleteNoteNotificationPayload(
                clinician_name=digest.clinician_name,
                recipient=recipient,
                incomplete_note_count=len(digest.records),
                rows=[
                    IncompleteNoteRow(
                        date_of_service=record.date_of_service,
                        client_display_name=record.client_display_name,
                        progress_note_status=record.progress_note_status,
                    )
                    for record in digest.records
                ],
            )
            rendered_html = self._factory.render("mindful_oregon.incomplete_note_notification", envelope, payload)
            slug = _slugify(digest.clinician_name)

            html_path = output_dir / f"{slug}_incomplete_notes.html"
            html_path.write_text(rendered_html, encoding="utf-8")
            html_paths.append(html_path)

            eml_path = output_dir / f"{slug}_incomplete_notes.eml"
            eml_path.write_text(
                _build_eml(
                    recipient=recipient,
                    sender=self._sender,
                    subject=subject,
                    rendered_html=rendered_html,
                ),
                encoding="utf-8",
            )
            eml_paths.append(eml_path)

        index_path = output_dir / "index.html"
        index_path.write_text(_index_html(html_paths, eml_paths, recipient), encoding="utf-8")
        return NotificationRenderResult(html_paths=html_paths, eml_paths=eml_paths, index_path=index_path)


def _build_eml(recipient: str, sender: str, subject: str, rendered_html: str) -> str:
    message = EmailMessage()
    message["To"] = recipient
    message["From"] = sender
    message["Subject"] = subject
    message.set_content("This email requires an HTML-capable email client.")
    message.add_alternative(rendered_html, subtype="html")
    return message.as_string()


def _index_html(html_paths: list[Path], eml_paths: list[Path], recipient: str) -> str:
    rows = "\n".join(
        f"<li><a href=\"{html_path.name}\">{html_path.stem}</a> "
        f"(<a href=\"{eml_path.name}\">email draft</a>)</li>"
        for html_path, eml_path in zip(html_paths, eml_paths, strict=True)
    )
    return f"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>Incomplete Note Notifications</title></head>
<body>
  <h1>Incomplete Note Notifications</h1>
  <p>Draft recipient: {recipient}</p>
  <ul>{rows}</ul>
</body>
</html>
"""


def _slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "unknown-clinician"
