"""Factory for validated Jinja email template rendering."""

from __future__ import annotations

from pathlib import Path
from typing import Any, TypeAlias

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape
from pydantic import BaseModel, ConfigDict

from iceflo_signal.models.email import (
    AlertReviewPayload,
    BaseCardPayload,
    ClinicianDigestPayload,
    EmailEnvelope,
    ExecSummaryPayload,
)

PayloadModel: TypeAlias = type[BaseModel]


class TemplateSpec(BaseModel):
    """Registry metadata for a renderable email template."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    template_id: str
    path: str
    payload_model: PayloadModel


DEFAULT_TEMPLATE_REGISTRY: dict[str, TemplateSpec] = {
    "mindful_oregon.base_card": TemplateSpec(
        template_id="mindful_oregon.base_card",
        path="clients/mindful_oregon/mindful_base_card.html.j2",
        payload_model=BaseCardPayload,
    ),
    "mindful_oregon.exec_summary": TemplateSpec(
        template_id="mindful_oregon.exec_summary",
        path="clients/mindful_oregon/mindful_exec_summary.html.j2",
        payload_model=ExecSummaryPayload,
    ),
    "mindful_oregon.clinician_digest": TemplateSpec(
        template_id="mindful_oregon.clinician_digest",
        path="clients/mindful_oregon/mindful_clinician_digest.html.j2",
        payload_model=ClinicianDigestPayload,
    ),
    "mindful_oregon.alert_review": TemplateSpec(
        template_id="mindful_oregon.alert_review",
        path="clients/mindful_oregon/mindful_alert_review.html.j2",
        payload_model=AlertReviewPayload,
    ),
}


class EmailTemplateFactory:
    """Render registered templates from validated envelope and payload models."""

    def __init__(
        self,
        template_dir: Path = Path("templates"),
        registry: dict[str, TemplateSpec] | None = None,
    ) -> None:
        self._registry = registry or DEFAULT_TEMPLATE_REGISTRY
        self._environment = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(["html", "xml"]),
            undefined=StrictUndefined,
        )

    def render(
        self,
        template_id: str,
        envelope: EmailEnvelope | dict[str, Any],
        payload: BaseModel | dict[str, Any],
    ) -> str:
        """Render a template after validating its shared envelope and payload."""

        spec = self.get_template_spec(template_id)
        envelope_model = self._validate_envelope(envelope)
        payload_model = self._validate_payload(spec, payload)

        template = self._environment.get_template(spec.path)
        return template.render(
            envelope=envelope_model.model_dump(),
            payload=payload_model.model_dump(),
        )

    def get_template_spec(self, template_id: str) -> TemplateSpec:
        """Return template metadata for a registered template ID."""

        try:
            return self._registry[template_id]
        except KeyError as exc:
            known_templates = ", ".join(sorted(self._registry))
            raise ValueError(f"Unknown template_id '{template_id}'. Known templates: {known_templates}") from exc

    @staticmethod
    def _validate_envelope(envelope: EmailEnvelope | dict[str, Any]) -> EmailEnvelope:
        if isinstance(envelope, EmailEnvelope):
            return envelope
        return EmailEnvelope.model_validate(envelope)

    @staticmethod
    def _validate_payload(spec: TemplateSpec, payload: BaseModel | dict[str, Any]) -> BaseModel:
        if isinstance(payload, spec.payload_model):
            return payload
        return spec.payload_model.model_validate(payload)
