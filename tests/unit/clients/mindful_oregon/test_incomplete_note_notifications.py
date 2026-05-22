from pathlib import Path

from iceflo_signal.delivery.clients.mindful_oregon import IncompleteNoteNotificationRenderer
from iceflo_signal.ingestion.clients.mindful_oregon.simple_practice import AppointmentStatusProcessor
from iceflo_signal.transforms.clients.mindful_oregon.simple_practice import IncompleteNoteTransformer


APPOINTMENT_STATUS_HEADER = (
    "Date of Service,Client,Clinician,Billing Code,Primary Insurance,Secondary Insurance,"
    "Rate per Unit,Units,Total Fee,Progress Note Status,Client Payment Status,Charge,Uninvoiced,"
    "Paid,Unpaid,Insurance Payment Status,Charge,Paid,Write Off,Unpaid"
)


def test_incomplete_note_transformer_excludes_locked_notes(tmp_path: Path) -> None:
    source = tmp_path / "appointment-status-report.csv"
    source.write_text(
        "\n".join(
            [
                APPOINTMENT_STATUS_HEADER,
                "2026-05-01,John Jones,Demo Clinician,90834,Demo Payer,,100,1,100,LOCKED,PAID,10,0,10,0,PAID,90,90,0,0",
                "5/2/2026 14:30,Joseph Johnson,Demo Clinician,90834,Demo Payer,,100,1,100,NO NOTE,UNPAID,10,0,0,10,UNBILLED,90,0,0,90",
                "5/3/2026 09:00,Avery Stone,Other Clinician,90834,Demo Payer,,100,1,100,DRAFT,UNPAID,10,0,0,10,UNBILLED,90,0,0,90",
            ]
        ),
        encoding="utf-8",
    )
    appointment_rows = AppointmentStatusProcessor().process(source)

    digests = IncompleteNoteTransformer().build_digests(appointment_rows)

    assert len(digests) == 2
    assert sum(len(digest.records) for digest in digests) == 2
    assert digests[0].records[0].client_display_name == "Jo Jo"
    assert digests[0].records[0].date_of_service == "05/02/2026 2:30 PM"
    assert digests[0].records[0].progress_note_status == "NO NOTE"


def test_incomplete_note_renderer_writes_clinician_drafts(tmp_path: Path) -> None:
    appointment_rows = [
        {
            "Date of Service": "5/2/2026 14:30",
            "Clinician": "Demo Clinician",
            "client_display_name": "Jo Jo",
            "client_key": "client-key-1",
            "Progress Note Status": "NO NOTE",
        }
    ]
    digests = IncompleteNoteTransformer().build_digests(appointment_rows)

    result = IncompleteNoteNotificationRenderer().render(
        digests=digests,
        output_dir=tmp_path,
        recipient="rdennis125@gmail.com",
        report_period="May 2026",
    )

    assert len(result.html_paths) == 1
    assert len(result.eml_paths) == 1
    html = result.html_paths[0].read_text(encoding="utf-8")
    eml = result.eml_paths[0].read_text(encoding="utf-8")

    assert "05/02/2026 2:30 PM" in html
    assert "Jo Jo" in html
    assert "NO NOTE" in html
    assert "John Jones" not in html
    assert "To: rdennis125@gmail.com" in eml
