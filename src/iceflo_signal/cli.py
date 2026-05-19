"""Small CLI for local pipeline runs."""

from __future__ import annotations

import argparse
from pathlib import Path

from iceflo_signal.delivery.clients.mindful_oregon import IncompleteNoteNotificationRenderer
from iceflo_signal.delivery.demo_renderer import render_template_demos
from iceflo_signal.ingestion.clients.mindful_oregon.simple_practice import AppointmentStatusProcessor
from iceflo_signal.pipeline import run_local_pipeline
from iceflo_signal.transforms.clients.mindful_oregon.simple_practice import IncompleteNoteTransformer


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
        default=Path("storage_sample/transformed/curated/template_demos"),
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
        default=Path("storage_sample/transformed/clients/mindful_oregon/simple_practice/curated/incomplete_note_notifications"),
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

    return 1
