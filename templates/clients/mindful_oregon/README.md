# Mindful Oregon-inspired HTML Email Layout Templates

These four templates are intended for the ICEFLO Signal email template factory.

## Files

- `mindful_base_card.html.j2` — default weekly report layout with metric cards.
- `mindful_exec_summary.html.j2` — corporate/admin summary with KPI list and callout section.
- `mindful_clinician_digest.html.j2` — clinician-specific digest with personal greeting and compact metrics.
- `mindful_alert_review.html.j2` — exception/review-needed layout with alert banner and table.
- `mindful_incomplete_note_notification.html.j2` — Mindful Oregon incomplete progress note notification.

## Template IDs

- `mindful_oregon.base_card`
- `mindful_oregon.exec_summary`
- `mindful_oregon.clinician_digest`
- `mindful_oregon.alert_review`
- `mindful_oregon.incomplete_note_notification`

## Context contract

Templates receive two top-level objects:

- `envelope` — shared email/report metadata such as `email_title`, `organization_name`, `report_title`, `report_period`, `intro_text`, `content_html`, and `footer_text`.
- `payload` — template-specific, validated data such as metric cards, KPI rows, clinician snapshot items, or alert tables.

## Suggested rendering flow

1. Generate curated CSV dataset.
2. Select recipients and report definition from config.
3. Select a template ID.
4. Validate the envelope and payload with Pydantic.
5. Render the template through the email template factory.
6. Send HTML body via Gmail API or another HIPAA-capable delivery path.
7. Log delivery status and template version.

## Notes

- Templates use inline CSS for email client compatibility.
- Avoid placing PHI in subject lines.
- Keep metric calculations outside the templates; templates should only render values already prepared by curated datasets.
