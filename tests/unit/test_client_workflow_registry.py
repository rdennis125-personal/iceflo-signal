from pathlib import Path

from iceflo_signal.config import load_client_manifest, load_client_workflows
from iceflo_signal.delivery.gmail import GmailSendResult
from iceflo_signal.workflows import run_configured_workflow


APPOINTMENT_STATUS_HEADER = (
    "Date of Service,Client,Clinician,Billing Code,Primary Insurance,Secondary Insurance,"
    "Rate per Unit,Units,Total Fee,Progress Note Status,Client Payment Status,Charge,Uninvoiced,"
    "Paid,Unpaid,Insurance Payment Status,Charge,Paid,Write Off,Unpaid"
)


def test_client_manifest_and_workflow_registry_load() -> None:
    manifest = load_client_manifest("mindful_oregon")
    workflows = load_client_workflows(Path("config/clients/mindful_oregon/workflows.json"))

    workflow = workflows.get_workflow("incomplete_note_notifications")

    assert manifest.client_key == "mindful_oregon"
    assert manifest.config_files.workflows == "workflows.json"
    assert workflow.source_system == "simple_practice"
    assert workflow.workflow_type == "simple_practice_incomplete_note_notifications"
    assert workflow.delivery is not None
    assert workflow.delivery.recipient_email == "rdennis125@gmail.com"
    assert workflow.delivery.sender_email == "rdennis125@gmail.com"
    assert "https://www.googleapis.com/auth/gmail.send" in workflow.delivery.scopes


def test_run_configured_workflow_uses_client_registry_paths(tmp_path: Path) -> None:
    incoming_dir = tmp_path / "sources" / "simple_practice" / "test" / "landing" / "incoming"
    incoming_dir.mkdir(parents=True)
    (incoming_dir / "appointment-status-report.csv").write_text(
        "\n".join(
            [
                APPOINTMENT_STATUS_HEADER,
                "5/1/2026 09:00,John Jones,Demo Clinician,90834,Demo Payer,,100,1,100,LOCKED,PAID,10,0,10,0,PAID,90,90,0,0",
                "5/2/2026 14:30,Joseph Johnson,Demo Clinician,90834,Demo Payer,,100,1,100,NO NOTE,UNPAID,10,0,0,10,UNBILLED,90,0,0,90",
            ]
        ),
        encoding="utf-8",
    )

    result = run_configured_workflow(
        client_key="mindful_oregon",
        workflow_id="incomplete_note_notifications",
        environment="test",
        recipient="rdennis125@gmail.com",
        storage_root=tmp_path,
    )

    assert result.records_processed == 1
    assert result.rendered_html_count == 1
    assert result.rendered_email_count == 1
    assert result.sent_email_count == 0
    assert result.output_prefix == "edw/test/presentation/incomplete_note_notifications"
    assert (
        tmp_path
        / "edw"
        / "test"
        / "presentation"
        / "incomplete_note_notifications"
        / "demo-clinician_incomplete_notes.html"
    ).exists()


def test_run_configured_workflow_can_send_rendered_emails(tmp_path: Path, monkeypatch) -> None:
    incoming_dir = tmp_path / "sources" / "simple_practice" / "test" / "landing" / "incoming"
    incoming_dir.mkdir(parents=True)
    (incoming_dir / "appointment-status-report.csv").write_text(
        "\n".join(
            [
                APPOINTMENT_STATUS_HEADER,
                "5/2/2026 14:30,Joseph Johnson,Demo Clinician,90834,Demo Payer,,100,1,100,NO NOTE,UNPAID,10,0,0,10,UNBILLED,90,0,0,90",
            ]
        ),
        encoding="utf-8",
    )
    sent_messages: list[str] = []

    class FakeGmailSender:
        def send_raw_message(self, message_text: str) -> GmailSendResult:
            sent_messages.append(message_text)
            return GmailSendResult(message_id="msg-1")

    monkeypatch.setattr(
        "iceflo_signal.workflows.registry.GmailSender.from_config",
        lambda config: FakeGmailSender(),
    )

    result = run_configured_workflow(
        client_key="mindful_oregon",
        workflow_id="incomplete_note_notifications",
        environment="test",
        storage_root=tmp_path,
        delivery_mode="send",
    )

    assert result.sent_email_count == 1
    assert len(sent_messages) == 1
    assert "To: rdennis125@gmail.com" in sent_messages[0]
    assert "From: rdennis125@gmail.com" in sent_messages[0]
