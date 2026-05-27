"""Small CLI for local pipeline runs."""

from __future__ import annotations

import argparse
from pathlib import Path

from iceflo_signal.config import load_client_data_layer_config, load_client_ingest_config, load_client_manifest
from iceflo_signal.delivery.clients.mindful_oregon import IncompleteNoteNotificationRenderer
from iceflo_signal.delivery.demo_renderer import render_template_demos
from iceflo_signal.ingestion.google_auth import build_google_credentials
from iceflo_signal.ingestion.google_drive import GoogleApiDriveClient, GoogleDriveIngestSource
from iceflo_signal.ingestion.clients.mindful_oregon.simple_practice import AppointmentStatusProcessor
from iceflo_signal.pipeline import run_local_pipeline
from iceflo_signal.storage import LocalFileRepository, build_repository
from iceflo_signal.transforms.clients.mindful_oregon.simple_practice import IncompleteNoteTransformer
from iceflo_signal.workflows import run_configured_workflow


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="iceflo_signal")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_local = subparsers.add_parser("run-local", help="Run the local CSV-to-curated pipeline.")
    run_local.add_argument("--input", required=True, type=Path, help="Path to the input CSV export.")
    run_local.add_argument("--output", required=True, type=Path, help="Base transformed output directory.")
    run_local.add_argument(
        "--template-dir",
        default=Path("templates"),
        type=Path,
        help="Directory containing Jinja2 templates.",
    )

    render_demo = subparsers.add_parser(
        "render-template-demo",
        help="Render browser-previewable demo HTML and .eml files for registered templates.",
    )
    render_demo.add_argument(
        "--recipient",
        default="rdennis125@gmail.com",
        help="Recipient address to include in demo context and generated .eml files.",
    )
    render_demo.add_argument(
        "--output",
        default=Path("storage_sample/edw/test/presentation/template_demos"),
        type=Path,
        help="Directory where demo HTML and .eml files will be written.",
    )
    render_demo.add_argument(
        "--template-dir",
        default=Path("templates"),
        type=Path,
        help="Directory containing Jinja2 templates.",
    )

    incomplete_notes = subparsers.add_parser(
        "render-incomplete-note-notifications",
        help="Render clinician dry-run notifications for appointment rows whose progress note is not LOCKED.",
    )
    incomplete_notes.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Path to the SimplePractice appointment-status-report CSV.",
    )
    incomplete_notes.add_argument(
        "--output",
        default=Path("storage_sample/edw/test/presentation/incomplete_note_notifications"),
        type=Path,
        help="Directory where notification HTML and .eml drafts will be written.",
    )
    incomplete_notes.add_argument(
        "--recipient",
        default="rdennis125@gmail.com",
        help="Fallback recipient address for generated .eml drafts.",
    )
    incomplete_notes.add_argument(
        "--report-period",
        default="Weekly SimplePractice export",
        help="Report period label shown in rendered notifications.",
    )
    incomplete_notes.add_argument(
        "--template-dir",
        default=Path("templates"),
        type=Path,
        help="Directory containing Jinja2 templates.",
    )

    sync_drive = subparsers.add_parser(
        "sync-google-drive",
        help="Download matching files from a configured Google Drive source into landing.",
    )
    sync_drive.add_argument(
        "--config",
        default=Path("config/clients/mindful_oregon/ingest_sources.json"),
        type=Path,
        help="Path to a client ingest-source config file.",
    )
    sync_drive.add_argument(
        "--data-layer-config",
        default=Path("config/clients/mindful_oregon/data_layers.json"),
        type=Path,
        help="Path to a client data-layer config file.",
    )
    sync_drive.add_argument(
        "--source-id",
        default="mindful_oregon_simple_practice_drive",
        help="Configured ingest source id to sync.",
    )
    sync_drive.add_argument(
        "--destination-repository",
        choices=["configured", "local"],
        default="configured",
        help="Repository to write downloaded files into. Use configured for Cloud Run/GCS.",
    )
    sync_drive.add_argument(
        "--storage-root",
        default=Path("storage_sample"),
        type=Path,
        help="Local storage root used when --destination-repository local.",
    )

    run_workflow = subparsers.add_parser(
        "run-workflow",
        help="Run a configured client workflow from the onboarding registry.",
    )
    run_workflow.add_argument("--client", required=True, help="Client key, such as mindful_oregon.")
    run_workflow.add_argument("--workflow", required=True, help="Workflow id from the client's workflows.json.")
    run_workflow.add_argument("--environment", default=None, help="Environment to run. Defaults to the client manifest.")
    run_workflow.add_argument(
        "--recipient",
        default="rdennis125@gmail.com",
        help="Recipient address used by notification preview workflows.",
    )
    run_workflow.add_argument(
        "--config-root",
        default=Path("config/clients"),
        type=Path,
        help="Root directory containing client onboarding configs.",
    )
    run_workflow.add_argument(
        "--storage-root",
        default=Path("storage_sample"),
        type=Path,
        help="Local storage root used by repository-backed local runs.",
    )
    run_workflow.add_argument(
        "--input-filename",
        default=None,
        help="Optional override for the configured workflow input filename.",
    )
    run_workflow.add_argument(
        "--repository",
        choices=["local", "configured"],
        default="local",
        help="Repository to use for workflow data. Use configured for Cloud Run/GCS.",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "run-local":
        result = run_local_pipeline(args.input, args.output, args.template_dir)
        print(f"Processed {result.rows_processed} rows from {result.source_filename}.")
        print(f"Outputs written under {args.output}.")
        return 0

    if args.command == "render-template-demo":
        result = render_template_demos(
            recipient=args.recipient,
            output_dir=args.output,
            template_dir=args.template_dir,
        )
        print(f"Rendered {len(result.html_paths)} HTML previews for {args.recipient}.")
        print(f"Rendered {len(result.eml_paths)} email drafts.")
        print(f"Open {result.index_path} in a browser.")
        return 0

    if args.command == "render-incomplete-note-notifications":
        appointment_rows = AppointmentStatusProcessor().process(args.input)
        digests = IncompleteNoteTransformer().build_digests(appointment_rows)
        result = IncompleteNoteNotificationRenderer(template_dir=args.template_dir).render(
            digests=digests,
            output_dir=args.output,
            recipient=args.recipient,
            report_period=args.report_period,
        )
        print(f"Found {sum(len(digest.records) for digest in digests)} incomplete-note appointments.")
        print(f"Rendered {len(result.html_paths)} clinician HTML previews.")
        print(f"Rendered {len(result.eml_paths)} clinician email drafts for {args.recipient}.")
        print(f"Open {result.index_path} in a browser.")
        return 0

    if args.command == "sync-google-drive":
        client_config = load_client_ingest_config(args.config)
        source_config = client_config.get_source(args.source_id)
        data_layer_config = load_client_data_layer_config(args.data_layer_config)
        if not source_config.repository_root_id:
            raise ValueError(f"{source_config.source_id} must define repository_root_id.")
        repository_root = data_layer_config.repository_root(source_config.repository_root_id)
        credentials = build_google_credentials(source_config)
        landing_repository = (
            build_repository(repository_root, google_drive_source=source_config)
            if args.destination_repository == "configured"
            else LocalFileRepository(args.storage_root)
        )
        downloaded = GoogleDriveIngestSource(
            config=source_config,
            drive_client=GoogleApiDriveClient(credentials),
            landing_repository=landing_repository,
        ).sync()
        print(f"Downloaded {len(downloaded)} files from {source_config.source_id}.")
        for item in downloaded:
            print(f"- {item.drive_file.name} -> {item.local_path}")
        return 0

    if args.command == "run-workflow":
        storage_repository = None
        if args.repository == "configured":
            manifest_dir = args.config_root / args.client
            manifest = load_client_manifest(args.client, config_root=args.config_root)
            data_layer_config = load_client_data_layer_config(manifest_dir / manifest.config_files.data_layers)
            ingest_config = load_client_ingest_config(manifest_dir / manifest.config_files.ingest_sources)
            environment = args.environment or manifest.default_environment
            edw_layer = data_layer_config.edw_layer(environment)
            repository_root = data_layer_config.repository_root(edw_layer.root_id)
            google_drive_source = _google_drive_source_for_repository(
                ingest_config.sources,
                repository_root.root_id,
                environment,
            )
            storage_repository = build_repository(
                repository_root,
                local_storage_root=args.storage_root,
                google_drive_source=google_drive_source,
            )
        result = run_configured_workflow(
            client_key=args.client,
            workflow_id=args.workflow,
            environment=args.environment,
            recipient=args.recipient,
            config_root=args.config_root,
            storage_repository=storage_repository,
            storage_root=args.storage_root,
            input_filename=args.input_filename,
        )
        print(f"Ran {result.workflow_id} for {result.client_key}/{result.environment}.")
        print(f"Processed {result.records_processed} records.")
        print(f"Rendered {result.rendered_html_count} HTML previews.")
        print(f"Rendered {result.rendered_email_count} email drafts.")
        print(f"Outputs written under {result.output_prefix}.")
        return 0

    return 1


def _google_drive_source_for_repository(sources, root_id: str, environment: str):
    for source in sources:
        if source.repository_root_id == root_id and source.environment == environment:
            return source
    return None
