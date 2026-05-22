"""Authentication helpers for Google Workspace APIs."""

from __future__ import annotations

from pathlib import Path

from iceflo_signal.config.ingest_sources import GoogleDriveSourceConfig


def build_google_credentials(config: GoogleDriveSourceConfig) -> object:
    """Build credentials for a Google Drive ingest source."""

    if config.auth_mode == "user_oauth":
        return _build_user_oauth_credentials(config)
    if config.auth_mode == "service_account":
        return _build_service_account_credentials(config)
    raise ValueError(f"Unsupported Google auth mode: {config.auth_mode}")


def _build_user_oauth_credentials(config: GoogleDriveSourceConfig) -> object:
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError as exc:
        raise RuntimeError(
            "User OAuth requires google-auth, google-auth-oauthlib, and google-auth-httplib2. "
            "Install project requirements before using Drive sync."
        ) from exc

    token_path = config.token_path()
    credentials = None
    if token_path and token_path.exists():
        credentials = Credentials.from_authorized_user_file(str(token_path), config.scopes)

    if credentials and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
    elif not credentials or not credentials.valid:
        client_secrets_path = _required_path(config.client_secrets_path(), "OAuth client secrets")
        flow = InstalledAppFlow.from_client_secrets_file(str(client_secrets_path), config.scopes)
        credentials = flow.run_local_server(port=0)

    if token_path:
        token_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            token_path.write_text(credentials.to_json(), encoding="utf-8")
        except OSError:
            # Secret-mounted files in Cloud Run are read-only. The refreshed credentials
            # remain valid for the current run even when they cannot be persisted.
            pass

    return credentials


def _build_service_account_credentials(config: GoogleDriveSourceConfig) -> object:
    try:
        from google.oauth2 import service_account
    except ImportError as exc:
        raise RuntimeError(
            "Service account auth requires google-auth. Install project requirements before using Drive sync."
        ) from exc

    service_account_path = _required_path(config.service_account_path(), "service account credentials")
    return service_account.Credentials.from_service_account_file(
        str(service_account_path),
        scopes=config.scopes,
    )


def _required_path(path: Path | None, label: str) -> Path:
    if not path:
        raise RuntimeError(f"Missing configured path for {label}.")
    if not path.exists():
        raise RuntimeError(f"Configured {label} file does not exist: {path}")
    return path
