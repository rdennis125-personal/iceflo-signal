"""Render clinician incomplete-note notification drafts."""

from __future__ import annotations

import re
from dataclasses import dataclass
from email.message import EmailMessage
from pathlib import Path

from iceflo_signal.delivery.template_factory import EmailTemplateFactory
from iceflo_signal.models.email import EmailEnvelope, IncompleteNoteNotificationPayload, IncompleteNoteRow
from iceflo_signal.storage import LocalFileRepository, ObjectRepository
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
        output_repository: ObjectRepository | None = None,
    ) -> NotificationRenderResult:
        """Write HTML previews and .eml drafts for clinician incomplete-note digests."""

        repository = output_repository or LocalFileRepository(output_dir)
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
            html_key = html_path.as_posix() if output_repository else html_path.name
            repository.write_text(html_key, rendered_html, content_type="text/html")
            html_paths.append(html_path)

            eml_path = output_dir / f"{slug}_incomplete_notes.eml"
            eml_key = eml_path.as_posix() if output_repository else eml_path.name
            repository.write_text(
                eml_key,
                _build_eml(
                    recipient=recipient,
                    sender=self._sender,
                    subject=subject,
                    rendered_html=rendered_html,
                ),
                content_type="message/rfc822",
            )
            eml_paths.append(eml_path)

        index_path = output_dir / "index.html"
        index_key = index_path.as_posix() if output_repository else index_path.name
        repository.write_text(index_key, _index_html(html_paths, eml_paths, recipient), content_type="text/html")
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
