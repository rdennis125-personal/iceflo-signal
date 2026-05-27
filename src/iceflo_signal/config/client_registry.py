"""Client onboarding registry configuration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel


class ClientConfigFiles(BaseModel):
    """Config files that define one client onboarding package."""

    data_layers: str
    ingest_sources: str
    workflows: str


class ClientManifest(BaseModel):
    """Top-level metadata for one onboarded ICEFLO Signal client."""

    client_key: str
    display_name: str
    default_environment: str = "test"
    config_files: ClientConfigFiles


class GmailDeliveryConfig(BaseModel):
    """Gmail delivery settings for a configured workflow."""

    provider: Literal["gmail"] = "gmail"
    recipient_email: str
    sender_email: str
    client_secrets_path_env: str = "ICEFLO_GOOGLE_OAUTH_CLIENT_SECRETS_PATH"
    token_path_env: str = "ICEFLO_MINDFUL_OREGON_GOOGLE_TOKEN_PATH"
    scopes: list[str] = ["https://www.googleapis.com/auth/gmail.send"]


class WorkflowConfig(BaseModel):
    """Configured workflow that can be executed for an onboarded client."""

    workflow_id: str
    workflow_type: Literal["simple_practice_incomplete_note_notifications"]
    enabled: bool = True
    source_system: str
    input_filename: str
    presentation_prefix: str
    recipient_mapping_id: str | None = None
    report_period: str = "Weekly export"
    template_dir: Path = Path("templates")
    delivery: GmailDeliveryConfig | None = None


class ClientWorkflowRegistry(BaseModel):
    """All configured workflows for one client."""

    client_key: str
    workflows: list[WorkflowConfig]

    def get_workflow(self, workflow_id: str) -> WorkflowConfig:
        """Return a workflow by id."""

        for workflow in self.workflows:
            if workflow.workflow_id == workflow_id:
                return workflow
        raise KeyError(f"Unknown workflow: {workflow_id}")


def load_client_manifest(client_key: str, config_root: Path = Path("config/clients")) -> ClientManifest:
    """Load one client manifest from the client config root."""

    manifest_path = config_root / client_key / "client.json"
    return ClientManifest.model_validate(json.loads(manifest_path.read_text(encoding="utf-8")))


def load_client_workflows(path: Path) -> ClientWorkflowRegistry:
    """Load one client's workflow registry."""

    return ClientWorkflowRegistry.model_validate(json.loads(path.read_text(encoding="utf-8")))
