import pytest
from pydantic import ValidationError

from iceflo_signal.delivery.template_factory import EmailTemplateFactory
from iceflo_signal.models.email import (
    AlertReviewPayload,
    BaseCardPayload,
    ClinicianDigestPayload,
    EmailEnvelope,
    ExecSummaryPayload,
    LabelValueItem,
)


def test_template_factory_renders_all_mindful_templates() -> None:
    factory = EmailTemplateFactory()
    envelope = EmailEnvelope(
        email_title="Weekly Documentation",
        organization_name="Mindful Oregon",
        report_title="Documentation Follow-up",
        report_period="May 4-10, 2026",
        intro_text="Please review your weekly documentation summary.",
        content_html="<p>Prepared from curated reporting data.</p>",
    )

    rendered = [
        factory.render(
            "mindful_oregon.base_card",
            envelope,
            BaseCardPayload(
                metric_cards=[
                    LabelValueItem(label="Incomplete", value=3, note="Needs review"),
                    LabelValueItem(label="Complete", value=12, note="Signed"),
                ]
            ),
        ),
        factory.render(
            "mindful_oregon.exec_summary",
            envelope,
            ExecSummaryPayload(
                executive_summary="Documentation completion improved this week.",
                kpi_grid=[LabelValueItem(label="Completion rate", value="92%", note="Synthetic demo")],
                callout_text="Prioritize aged documentation.",
            ),
        ),
        factory.render(
            "mindful_oregon.clinician_digest",
            envelope,
            ClinicianDigestPayload(
                clinician_name="Avery Stone",
                snapshot_items=[LabelValueItem(label="Open items", value=1)],
            ),
        ),
        factory.render(
            "mindful_oregon.alert_review",
            envelope,
            AlertReviewPayload(
                alert_title="Review needed",
                alert_message="Some sessions need documentation review.",
                table_columns=["Session", "Status"],
                table_rows=[["SYN-1002", "Incomplete"]],
            ),
        ),
    ]

    assert all("<!doctype html>" in html for html in rendered)
    assert "Mindful Oregon" in rendered[0]
    assert "Mindful Oregon" in rendered[1]
    assert "Avery Stone" in rendered[2]
    assert "Prepared from curated reporting data." in rendered[0]
    assert "SYN-1002" in rendered[3]


def test_template_factory_rejects_payload_for_wrong_template() -> None:
    factory = EmailTemplateFactory()

    with pytest.raises(ValidationError):
        factory.render(
            "mindful_oregon.clinician_digest",
            EmailEnvelope(),
            BaseCardPayload(metric_cards=[LabelValueItem(label="Open", value=1)]),
        )


def test_template_factory_rejects_unknown_template_id() -> None:
    factory = EmailTemplateFactory()

    with pytest.raises(ValueError, match="Unknown template_id"):
        factory.render("unknown.template", EmailEnvelope(), {})
