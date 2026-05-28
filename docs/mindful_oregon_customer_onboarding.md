# Mindful Oregon Customer Onboarding Playbook

This playbook is for Mindful Oregon. It describes what ICEFLO Signal needs from the customer to configure the first SimplePractice incomplete-note notification workflow.

## What ICEFLO Signal Does

ICEFLO Signal reads manually exported SimplePractice CSV files, transforms them through a privacy-conscious reporting flow, and prepares weekly incomplete-note notification emails.

For the first use case, the workflow filters the SimplePractice appointment status export to appointments where:

```text
Progress Note Status is not LOCKED
```

The email output includes:

- Date of Service
- Obfuscated Client display value
- Progress Note Status

Client names are not shown directly in presentation outputs. For example, `John Jones` appears as `Jo Jo`. Similar display values may repeat, but ICEFLO preserves unique internal records for reporting continuity.

## Storage Options

Mindful Oregon controls the data locations. ICEFLO Signal can be configured against supported repository types.

Current supported options:

- Google Drive source landing folder
- GCS client data root

Future-supported pattern:

- Google Drive data root
- Client-provided database or warehouse implementation

For the first test, Mindful Oregon selected Google Drive for the source landing folder. The current deployed test writes transformed outputs to the configured Mindful Oregon data root.

## Folder Inputs Needed

For each source system, ICEFLO needs a landing location where exports will be placed.

For SimplePractice test:

```text
SimplePractice test landing folder
  Purpose: customer drops manually exported CSV files here
  Access needed: read access for ingest; write access only if archive/rejected handling is enabled later
```

For the client data root:

```text
Mindful Oregon test data root
  Purpose: stores landing copies, EDW layers, curated outputs, and presentation artifacts
  Access needed: read/write access for ICEFLO runtime
```

Expected logical structure inside the data root:

```text
{mindful_oregon_data_root}
  /sources
    /simple_practice
      /test
        /landing
          /incoming
          /archive
          /rejected
  /edw
    /test
      /raw
      /normalized
      /facts
      /dimensions
      /curated
      /presentation
  /utility
    /test
      /config
      /schemas
      /templates
      /reference
```

The landing folder may be outside the data root so customer-side export tasks and security can be managed separately.

## Access Options

### Option 1: User OAuth

Use this when a named Google user account has access to the Drive folder.

Customer provides:

- Google account email that owns or can access the folder.
- Shared folder link or folder ID for the SimplePractice landing folder.
- Confirmation that the account is allowed to authorize ICEFLO Signal for Drive and email sending.

ICEFLO configures:

- OAuth client
- OAuth token
- Secret Manager entries
- Cloud Run runtime mounts and environment variables

### Option 2: Service Account

Use this when the customer can share the folder with an ICEFLO-provided service account or can create their own service account and grant access.

Customer provides:

- Service account email or JSON key management approach, depending on ownership model.
- Folder sharing confirmation.
- Any customer-side restrictions or audit requirements.

This is preferred for production when available because it avoids a personal user token dependency.

## Email Sending Inputs Needed

For the test workflow, ICEFLO needs:

```text
sender_email: account shown in the From field
recipient_email: test recipient for all generated emails
```

For production, ICEFLO will eventually need:

- Approved sender account.
- Provider or clinician recipient mapping.
- Confirmation of whether replies should go to the sender, a shared inbox, or a no-reply address.
- Approval of the subject line and body template wording.

The first test can send every notification to one configured recipient. Production should use customer-approved recipient mappings.

## SimplePractice Export Requirements

For incomplete-note notifications, place this export in the SimplePractice landing folder:

```text
appointment-status-report.csv
```

The file must include:

- Clinician
- Date of Service
- Client
- Progress Note Status

Do not manually edit column headers unless agreed with ICEFLO. If SimplePractice export formats change, notify ICEFLO before the next scheduled run.

## Customer Validation Checklist

Before the first test run:

- Confirm the SimplePractice landing folder is shared correctly.
- Upload a synthetic or approved test export.
- Confirm sender and recipient email addresses.
- Review and approve the email template tone.
- Confirm whether test emails can be sent to the configured recipient.

After the test run:

- Confirm the test email was received.
- Confirm the email wording is acceptable.
- Confirm incomplete-note rows match expectations.
- Confirm client names are obfuscated in the output.
- Confirm no unintended PHI appears in the email body.

## Production Readiness Questions

Before production scheduling, decide:

- Who owns the recurring SimplePractice export task?
- What day and time should the weekly export be available?
- What day and time should notifications send?
- Should ICEFLO archive processed source files?
- Who receives send failure alerts?
- Who approves provider recipient mappings?
- How long should generated outputs be retained?
