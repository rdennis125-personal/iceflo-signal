"""Local orchestration for the initial ICEFLO Signal pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from io import StringIO
from pathlib import Path

from iceflo_signal.delivery.renderer import render_clinician_followups
from iceflo_signal.ingestion.csv_reader import read_sessions_csv_from_repository
from iceflo_signal.logging.structured import get_logger
from iceflo_signal.storage import LocalFileRepository, ObjectRepository
from iceflo_signal.transforms.documentation import build_clinician_documentation_status
from iceflo_signal.transforms.sessions import (
    build_dim_clinician,
    build_dim_date,
    build_fact_documentation_status,
    build_fact_session,
    normalize_sessions,
)
from iceflo_signal.validation.sessions import validate_session_export

logger = get_logger(__name__)


@dataclass(frozen=True)
class PipelineResult:
    """Summary of a local pipeline execution."""

    source_filename: str
    rows_processed: int


def run_local_pipeline(input_path: Path, output_path: Path, template_dir: Path = Path("templates")) -> PipelineResult:
    """Run the local sample pipeline and write layered CSV and HTML outputs."""

    return run_pipeline(
        input_key=input_path.as_posix(),
        output_prefix="",
        input_repository=LocalFileRepository(Path(".")),
        output_repository=LocalFileRepository(output_path),
        template_dir=template_dir,
    )


def run_pipeline(
    input_key: str,
    output_prefix: str,
    input_repository: ObjectRepository,
    output_repository: ObjectRepository,
    template_dir: Path = Path("templates"),
) -> PipelineResult:
    """Run the sample pipeline against an injected storage repository."""

    raw = read_sessions_csv_from_repository(input_repository, input_key)
    validation = validate_session_export(raw)
    if not validation.is_valid:
        errors = "; ".join(issue.message for issue in validation.issues)
        raise ValueError(f"Input validation failed: {errors}")

    normalized = normalize_sessions(raw)
    dim_clinician = build_dim_clinician(normalized)
    dim_date = build_dim_date(normalized)
    fact_session = build_fact_session(normalized)
    fact_documentation = build_fact_documentation_status(normalized)
    curated = build_clinician_documentation_status(normalized)

    _write_csv(output_repository, _join_key(output_prefix, "raw/sessions_raw.csv"), raw)
    _write_csv(output_repository, _join_key(output_prefix, "normalized/sessions_normalized.csv"), normalized)
    _write_csv(output_repository, _join_key(output_prefix, "dimensions/dim_clinician.csv"), dim_clinician)
    _write_csv(output_repository, _join_key(output_prefix, "dimensions/dim_date.csv"), dim_date)
    _write_csv(output_repository, _join_key(output_prefix, "facts/fact_session.csv"), fact_session)
    _write_csv(output_repository, _join_key(output_prefix, "facts/fact_documentation_status.csv"), fact_documentation)
    _write_csv(output_repository, _join_key(output_prefix, "curated/curated_clinician_documentation_status.csv"), curated)

    render_clinician_followups(
        curated,
        template_dir=template_dir,
        output_dir=Path(_join_key(output_prefix, "curated/notifications")),
        output_repository=output_repository,
    )

    logger.info(
        "pipeline_completed",
        extra={"source_filename": Path(input_key).name, "rows_processed": len(raw)},
    )
    return PipelineResult(source_filename=Path(input_key).name, rows_processed=len(raw))


def _write_csv(repository: ObjectRepository, key: str, frame) -> None:
    buffer = StringIO()
    frame.to_csv(buffer, index=False)
    repository.write_text(key, buffer.getvalue(), content_type="text/csv")


def _join_key(prefix: str, suffix: str) -> str:
    if not prefix:
        return suffix.lstrip("/")
    return f"{prefix.rstrip('/')}/{suffix.lstrip('/')}"
