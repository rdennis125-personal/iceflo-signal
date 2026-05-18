"""Small CLI for local pipeline runs."""

from __future__ import annotations

import argparse
from pathlib import Path

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

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "run-local":
        result = run_local_pipeline(args.input, args.output, args.template_dir)
        print(f"Processed {result.rows_processed} rows from {result.source_filename}.")
        print(f"Outputs written under {args.output}.")
        return 0

    return 1
