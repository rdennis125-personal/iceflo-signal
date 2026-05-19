from pathlib import Path

import pytest

from iceflo_signal.ingestion.clients.mindful_oregon.simple_practice import (
    AppointmentStatusProcessor,
    ClientAttendanceProcessor,
    ClientDetailsProcessor,
)


def test_processor_obfuscates_client_name_and_keeps_unique_key(tmp_path: Path) -> None:
    source = tmp_path / "appointment-status-report.csv"
    source.write_text(
        "\n".join(
            [
                "Date of Service,Client,Clinician,Billing Code,Primary Insurance,Secondary Insurance,Rate per Unit,Units,Total Fee,Progress Note Status,Client Payment Status,Charge,Uninvoiced,Paid,Unpaid,Insurance Payment Status,Charge,Paid,Write Off,Unpaid",
                "2026-05-01,John Jones,Demo Clinician,90834,Demo Payer,,100,1,100,Complete,Paid,100,0,100,0,Paid,80,80,20,0",
                "2026-05-02,Joseph Johnson,Demo Clinician,90834,Demo Payer,,100,1,100,Complete,Paid,100,0,100,0,Paid,80,80,20,0",
            ]
        ),
        encoding="utf-8",
    )

    rows = AppointmentStatusProcessor().process(source)

    assert rows[0]["client_display_name"] == "Jo Jo"
    assert rows[1]["client_display_name"] == "Jo Jo"
    assert rows[0]["client_key"] != rows[1]["client_key"]
    assert "Client" not in rows[0]
    assert rows[0]["client_responsibility_charge"] == "100"
    assert rows[0]["client_responsibility_unpaid"] == "0"
    assert rows[0]["insurance_responsibility_charge"] == "80"
    assert rows[0]["insurance_responsibility_unpaid"] == "0"
    assert "Charge__2" not in rows[0]


def test_processor_obfuscates_contact_name(tmp_path: Path) -> None:
    source = tmp_path / "client_details_report.csv"
    source.write_text(
        "\n".join(
            [
                "Client,Client type,Date added,Primary clinician,Last appointment,Next appointment,Address,City,State,ZIP,Phone number,Email,Contact name,Contact phone,Contact email,Primary insurance,Insurance ID,Status",
                "Avery Stone,Individual,2026-01-01,Demo Clinician,,,,Portland,OR,97201,555-0000,obfuscated@example.test,Jordan Lee,555-1111,contact@example.test,Demo Payer,ABC123,Active",
            ]
        ),
        encoding="utf-8",
    )

    row = ClientDetailsProcessor().process(source)[0]

    assert row["client_display_name"] == "Av St"
    assert row["contact_name_display_name"] == "Jo Le"
    assert "Client" not in row
    assert "Contact name" not in row
    assert row["Contact phone"] == "555-1111"


def test_processor_rejects_missing_expected_column(tmp_path: Path) -> None:
    source = tmp_path / "bad.csv"
    source.write_text("Client,Clinician\nJohn Jones,Demo Clinician\n", encoding="utf-8")

    with pytest.raises(ValueError, match="missing columns"):
        AppointmentStatusProcessor().process(source)


def test_client_attendance_processor_skips_summary_row(tmp_path: Path) -> None:
    source = tmp_path / "client_attendance_report.csv"
    source.write_text(
        "\n".join(
            [
                "client_name,clinician_name,date_of_service,office_name,status",
                "230 clients,9 clinicians,807 appointments,1 office,5 statuses",
                "John Jones,Demo Clinician,2026-05-01,Telehealth Video,Show",
            ]
        ),
        encoding="utf-8",
    )

    rows = ClientAttendanceProcessor().process(source)

    assert len(rows) == 1
    assert rows[0]["client_name_display_name"] == "Jo Jo"
    assert rows[0]["clinician_name"] == "Demo Clinician"
