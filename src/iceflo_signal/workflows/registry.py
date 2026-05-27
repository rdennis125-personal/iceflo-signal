"""Runtime execution for configured client workflows."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from iceflo_signal.config import (
    WorkflowConfig,
    load_client_data_layer_config,
    load_client_manifest,
    load_client_workflows,
)
from iceflo_signal.delivery.clients.mindful_oregon import IncompleteNoteNotificationRenderer
from iceflo_signal.delivery.gmail import GmailSender
from iceflo_signal.ingestion.clients.mindful_oregon.simple_practice import AppointmentStatusProcessor
from iceflo_signal.storage import LocalFileRepository, ObjectRepository
from iceflo_signal.transforms.clients.mindful_oregon.simple_practice import IncompleteNoteTransformer


@dataclass(frozen=True)
class WorkflowRunResult:
    """Summary of a configured workflow run."""

    client_key: str
    environment: str
    workflow_id: str
    records_processed: int
    rendered_html_count: int
    rendered_email_count: int
    sent_email_count: int
    output_prefix: str


def run_configured_workflow(
    client_key: str,
    workflow_id: str,
    environment: str | None = None,
    recipient: str | None = None,
    delivery_mode: str = "dry_run",
    config_root: Path = Path("config/clients"),
    storage_repository: ObjectRepository | None = None,
    storage_root: Path = Path("storage_sample"),
    input_filename: str | None = None,
) -> WorkflowRunResult:
    """Resolve and execute a workflow from client configuration."""

    manifest = load_client_manifest(client_key, config_root=config_root)
    resolved_environment = environment or manifest.default_environment
    client_config_dir = config_root / client_key
    data_layers = load_client_data_layer_config(client_config_dir / manifest.config_files.data_layers)
    workflows = load_client_workflows(client_config_dir / manifest.config_files.workflows)
    workflow = workflows.get_workflow(workflow_id)

    if not workflow.enabled:
        raise ValueError(f"Workflow is disabled: {workflow_id}")
    if workflow.workflow_type == "simple_practice_incomplete_note_notifications":
        repository = storage_repository or LocalFileRepository(storage_root)
        return _run_simple_practice_incomplete_note_notifications(
            client_key=client_key,
            environment=resolved_environment,
            workflow=workflow,
            recipient=recipient or (workflow.delivery.recipient_email if workflow.delivery else "rdennis125@gmail.com"),
            data_layers=data_layers,
            repository=repository,
            input_filename=input_filename,
            delivery_mode=delivery_mode,
        )

    raise ValueError(f"Unsupported workflow type: {workflow.workflow_type}")


def _run_simple_practice_incomplete_note_notifications(
    client_key: str,
    environment: str,
    workflow: WorkflowConfig,
    recipient: str,
    data_layers,
    repository: ObjectRepository,
    input_filename: str | None,
    delivery_mode: str,
) -> WorkflowRunResult:
    source_layer = data_layers.source_layer(workflow.source_system, environment)
    edw_layer = data_layers.edw_layer(environment)
    filename = input_filename or workflow.input_filename
    input_key = _join_key(source_layer.incoming_prefix, filename)
    presentation_prefix = edw_layer.prefixes["presentation"]
    output_prefix = _join_key(presentation_prefix, workflow.presentation_prefix)

    rows = AppointmentStatusProcessor(client_namespace=client_key).process_from_repository(repository, input_key)
    digests = IncompleteNoteTransformer().build_digests(rows)
    result = IncompleteNoteNotificationRenderer(
        template_dir=workflow.template_dir,
        sender=workflow.delivery.sender_email if workflow.delivery else "no-reply@iceflo-signal.example",
    ).render(
        digests=digests,
        output_dir=Path(output_prefix),
        recipient=recipient,
        report_period=workflow.report_period,
        output_repository=repository,
    )
    sent_email_count = 0
    if delivery_mode == "send":
        if not workflow.delivery:
            raise ValueError(f"Workflow {workflow.workflow_id} does not define delivery settings.")
        sender = GmailSender.from_config(workflow.delivery)
        for eml_path in result.eml_paths:
            sender.send_raw_message(repository.read_text(eml_path.as_posix()))
            sent_email_count += 1
    elif delivery_mode != "dry_run":
        raise ValueError(f"Unsupported delivery mode: {delivery_mode}")

    return WorkflowRunResult(
        client_key=client_key,
        environment=environment,
        workflow_id=workflow.workflow_id,
        records_processed=sum(len(digest.records) for digest in digests),
        rendered_html_count=len(result.html_paths),
        rendered_email_count=len(result.eml_paths),
        sent_email_count=sent_email_count,
        output_prefix=output_prefix,
    )


def _join_key(prefix: str, suffix: str) -> str:
    return f"{prefix.rstrip('/')}/{suffix.lstrip('/')}"
