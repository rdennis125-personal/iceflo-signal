from pathlib import Path

import pytest

from iceflo_signal.delivery.clients.mindful_oregon import IncompleteNoteNotificationRenderer
from iceflo_signal.ingestion.clients.mindful_oregon.simple_practice import (
    AppointmentStatusProcessor,
    ClientAttendanceProcessor,
    ClientDemographicsProcessor,
    ClientDetailsProcessor,
    ClientEmailsProcessor,
    ClientPhoneSmsRemindersProcessor,
    InsuranceAgingProcessor,
    InsuranceClaimsProcessor,
    InsurancePaymentReportsProcessor,
    InsuranceStatusChecksProcessor,
    UnpaidInsuranceAppointmentsProcessor,
)
from iceflo_signal.transforms.clients.mindful_oregon.simple_practice import IncompleteNoteTransformer


UPLOAD_DIR = Path.home() / "Downloads"


UPLOADED_EXPORTS = [
    ("client_phone_sms_reminders_report.csv", ClientPhoneSmsRemindersProcessor),
    ("client_emails_report.csv", ClientEmailsProcessor),
    ("unpaid-insurance-appointments-report.csv", UnpaidInsuranceAppointmentsProcessor),
    ("insurance_claims_report.csv", InsuranceClaimsProcessor),
    ("insurance_payment_reports_report.csv", InsurancePaymentReportsProcessor),
    ("insurance_status_checks_report.csv", InsuranceStatusChecksProcessor),
    ("appointment-status-report.csv", AppointmentStatusProcessor),
    ("client_details_report.csv", ClientDetailsProcessor),
    ("client_attendance_report.csv", ClientAttendanceProcessor),
    ("client_demographics_report.csv", ClientDemographicsProcessor),
    ("insurance_aging_report.csv", InsuranceAgingProcessor),
]


@pytest.mark.parametrize(("filename", "processor_class"), UPLOADED_EXPORTS)
def test_uploaded_simple_practice_examples_are_processable(filename: str, processor_class: type) -> None:
    source = UPLOAD_DIR / filename
    if not source.exists():
        pytest.skip(f"Uploaded example not available: {source}")

    rows = processor_class().process(source)

    assert rows, f"{filename} should produce transformed rows"
    assert all(row["source_filename"] == filename for row in rows)
    assert all(row["source_hash"] for row in rows)


def test_uploaded_appointment_status_drives_incomplete_note_notifications(tmp_path: Path) -> None:
    source = UPLOAD_DIR / "appointment-status-report.csv"
    if not source.exists():
        pytest.skip(f"Uploaded example not available: {source}")

    appointment_rows = AppointmentStatusProcessor().process(source)
    digests = IncompleteNoteTransformer().build_digests(appointment_rows)

    assert sum(len(digest.records) for digest in digests) == 113
    assert len(digests) == 9
    assert all(
        record.progress_note_status.upper() != "LOCKED"
        for digest in digests
        for record in digest.records
    )

    result = IncompleteNoteNotificationRenderer().render(
        digests=digests,
        output_dir=tmp_path,
        recipient="rdennis125@gmail.com",
        report_period="Uploaded appointment status export",
    )

    assert len(result.html_paths) == 9
    assert len(result.eml_paths) == 9
    first_preview = result.html_paths[0].read_text(encoding="utf-8")
    assert "Incomplete note snapshot" in first_preview
    assert "Please review the appointments below" in first_preview
    assert "Progress Note Status" in first_preview
    assert "To: rdennis125@gmail.com" in result.eml_paths[0].read_text(encoding="utf-8")
