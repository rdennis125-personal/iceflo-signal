"""Configuration loading lives here as report definitions grow."""

from iceflo_signal.config.ingest_sources import (
    ClientDataLayerConfig,
    ClientIngestSourceConfig,
    EdwLayerConfig,
    GoogleDriveSourceConfig,
    RepositoryRootConfig,
    SourceLayerConfig,
    load_client_data_layer_config,
    load_client_ingest_config,
)
from iceflo_signal.config.client_registry import (
    ClientManifest,
    ClientWorkflowRegistry,
    WorkflowConfig,
    load_client_manifest,
    load_client_workflows,
)

__all__ = [
    "ClientDataLayerConfig",
    "ClientIngestSourceConfig",
    "ClientManifest",
    "ClientWorkflowRegistry",
    "EdwLayerConfig",
    "GoogleDriveSourceConfig",
    "RepositoryRootConfig",
    "SourceLayerConfig",
    "WorkflowConfig",
    "load_client_data_layer_config",
    "load_client_ingest_config",
    "load_client_manifest",
    "load_client_workflows",
]
