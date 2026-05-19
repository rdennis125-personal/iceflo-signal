"""Export-specific SimplePractice processors for Mindful Oregon."""

from __future__ import annotations

from iceflo_signal.ingestion.clients.mindful_oregon.simple_practice.base import (
    SimplePracticeCsvProcessor,
    SimplePracticeExportDefinition,
)


class ClientPhoneSmsRemindersProcessor(SimplePracticeCsvProcessor):
    definition = SimplePracticeExportDefinition(
        export_name="client_phone_sms_reminders",
        expected_columns=("Date", "Primary Clinician", "Client", "Type", "Status"),
        client_name_columns=("Client",),
    )


class ClientEmailsProcessor(SimplePracticeCsvProcessor):
    definition = SimplePracticeExportDefinition(
        export_name="client_emails",
        expected_columns=("Date", "Primary Clinician", "Client", "Status", "To", "Subject"),
        client_name_columns=("Client",),
    )


class UnpaidInsuranceAppointmentsProcessor(SimplePracticeCsvProcessor):
    definition = SimplePracticeExportDefinition(
        export_name="unpaid_insurance_appointments",
        expected_columns=(
            "Date",
            "Client",
            "Clearinghouse Reference",
            "Payer Claim",
            "Billed",
            "Co-Pay",
            "Ins. Billed",
            "Ins. Paid",
            "Ins. Balance",
        ),
        client_name_columns=("Client",),
    )


class InsuranceClaimsProcessor(SimplePracticeCsvProcessor):
    definition = SimplePracticeExportDefinition(
        export_name="insurance_claims",
        expected_columns=("Date Submitted", "Client", "Status", "Payer", "Clearinghouse Reference", "Payer Claim"),
        client_name_columns=("Client",),
    )


class InsurancePaymentReportsProcessor(SimplePracticeCsvProcessor):
    definition = SimplePracticeExportDefinition(
        export_name="insurance_payment_reports",
        expected_columns=(
            "Date Received",
            "Client",
            "Payer",
            "Amount",
            "Clearinghouse Reference",
            "Payer Claim",
            "Payment Reference",
            "Payment Status",
        ),
        client_name_columns=("Client",),
    )


class InsuranceStatusChecksProcessor(SimplePracticeCsvProcessor):
    definition = SimplePracticeExportDefinition(
        export_name="insurance_status_checks",
        expected_columns=("Date Requested", "Client", "Status", "Payer"),
        client_name_columns=("Client",),
    )


class AppointmentStatusProcessor(SimplePracticeCsvProcessor):
    definition = SimplePracticeExportDefinition(
        export_name="appointment_status",
        expected_columns=(
            "Date of Service",
            "Client",
            "Clinician",
            "Billing Code",
            "Primary Insurance",
            "Secondary Insurance",
            "Rate per Unit",
            "Units",
            "Total Fee",
            "Progress Note Status",
            "Client Payment Status",
            "Charge",
            "Uninvoiced",
            "Paid",
            "Unpaid",
            "Insurance Payment Status",
            "Write Off",
        ),
        client_name_columns=("Client",),
    )

    def transform_row(self, row: dict[str, str]) -> dict[str, object]:
        transformed = super().transform_row(row)
        responsibility_columns = {
            "Charge": "client_responsibility_charge",
            "Paid": "client_responsibility_paid",
            "Unpaid": "client_responsibility_unpaid",
            "Charge__2": "insurance_responsibility_charge",
            "Paid__2": "insurance_responsibility_paid",
            "Unpaid__2": "insurance_responsibility_unpaid",
        }
        for source_column, target_column in responsibility_columns.items():
            if source_column in transformed:
                transformed[target_column] = transformed.pop(source_column)
        return transformed


class ClientDetailsProcessor(SimplePracticeCsvProcessor):
    definition = SimplePracticeExportDefinition(
        export_name="client_details",
        expected_columns=(
            "Client",
            "Client type",
            "Date added",
            "Primary clinician",
            "Last appointment",
            "Next appointment",
            "Address",
            "City",
            "State",
            "ZIP",
            "Phone number",
            "Email",
            "Contact name",
            "Contact phone",
            "Contact email",
            "Primary insurance",
            "Insurance ID",
            "Status",
        ),
        client_name_columns=("Client", "Contact name"),
    )


class ClientAttendanceProcessor(SimplePracticeCsvProcessor):
    definition = SimplePracticeExportDefinition(
        export_name="client_attendance",
        expected_columns=("client_name", "clinician_name", "date_of_service", "office_name", "status"),
        client_name_columns=("client_name",),
    )

    def should_skip_row(self, row: dict[str, str]) -> bool:
        """Skip the SimplePractice summary row at the top of attendance exports."""

        return (
            str(row.get("client_name", "")).strip().endswith(" clients")
            and str(row.get("clinician_name", "")).strip().endswith(" clinicians")
            and str(row.get("date_of_service", "")).strip().endswith(" appointments")
        )


class ClientDemographicsProcessor(SimplePracticeCsvProcessor):
    definition = SimplePracticeExportDefinition(
        export_name="client_demographics",
        expected_columns=(
            "Client",
            "Contact",
            "Age",
            "Date of birth",
            "Sex",
            "Gender identity",
            "Race",
            "Relationship status",
            "Employment status",
            "Preferred language",
            "City",
            "ZIP",
        ),
        client_name_columns=("Client", "Contact"),
    )


class InsuranceAgingProcessor(SimplePracticeCsvProcessor):
    definition = SimplePracticeExportDefinition(
        export_name="insurance_aging",
        expected_columns=("Insurance Payer", "Unbilled", "Total Charges", "Due 30 days", "Due 60 days", "Balance Due"),
    )
