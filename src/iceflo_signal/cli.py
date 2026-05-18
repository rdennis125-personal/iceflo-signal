"""Small CLI for local pipeline runs."""

from __future__ import annotations

import argparse
from pathlib import Path

from iceflo_signal.delivery.demo_renderer import render_template_demos
from iceflo_signal.pipeline import run_local_pipeline


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

    return 1
