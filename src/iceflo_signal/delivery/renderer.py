"""Render local HTML files for clinician follow-up notifications."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
from jinja2 import Environment, FileSystemLoader, select_autoescape


def render_clinician_followups(curated: pd.DataFrame, template_dir: Path, output_dir: Path) -> list[Path]:
    """Render one dry-run HTML notification per clinician."""

    output_dir.mkdir(parents=True, exist_ok=True)
    environment = Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = environment.get_template("content/clinician_documentation_followup.html.j2")

    rendered_paths: list[Path] = []
    for row in curated.to_dict(orient="records"):
        filename = f"{_slugify(row['clinician_id'])}_documentation_followup.html"
        output_path = output_dir / filename
        output_path.write_text(template.render(report=row), encoding="utf-8")
        rendered_paths.append(output_path)

    return rendered_paths


def _slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
