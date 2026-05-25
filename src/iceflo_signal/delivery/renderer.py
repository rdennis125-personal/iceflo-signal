"""Render local HTML files for clinician follow-up notifications."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
from jinja2 import Environment, FileSystemLoader, select_autoescape

from iceflo_signal.storage import LocalFileRepository, ObjectRepository


def render_clinician_followups(
    curated: pd.DataFrame,
    template_dir: Path,
    output_dir: Path,
    output_repository: ObjectRepository | None = None,
) -> list[Path]:
    """Render one dry-run HTML notification per clinician."""

    repository = output_repository or LocalFileRepository(output_dir)
    environment = Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = environment.get_template("content/clinician_documentation_followup.html.j2")

    rendered_paths: list[Path] = []
    for row in curated.to_dict(orient="records"):
        filename = f"{_slugify(row['clinician_id'])}_documentation_followup.html"
        output_path = output_dir / filename
        output_key = output_path.as_posix() if output_repository else filename
        repository.write_text(output_key, template.render(report=row), content_type="text/html")
        rendered_paths.append(output_path)

    return rendered_paths


def _slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
