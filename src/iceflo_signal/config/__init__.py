"""Configuration loading lives here as report definitions grow."""

from iceflo_signal.config.ingest_sources import (
    ClientIngestSourceConfig,
    GoogleDriveSourceConfig,
    load_client_ingest_config,
)

__all__ = [
    "ClientIngestSourceConfig",
    "GoogleDriveSourceConfig",
    "load_client_ingest_config",
]
