"""Gmail delivery adapter for rendered email drafts."""

from __future__ import annotations

import base64
import os
from dataclasses import dataclass
from pathlib import Path

from iceflo_signal.config import GmailDeliveryConfig
from iceflo_signal.ingestion.google_auth import build_user_oauth_credentials


@dataclass(frozen=True)
class GmailSendResult:
    """Result metadata from Gmail API message send."""

    message_id: str
    thread_id: str | None = None


class GmailSender:
    """Send RFC 822 email messages through the Gmail API."""

    def __init__(self, credentials: object, user_id: str = "me") -> None:
        try:
            from googleapiclient.discovery import build
        except ImportError as exc:
            raise RuntimeError(
                "Gmail delivery requires google-api-python-client. "
                "Install project requirements before using Gmail delivery."
            ) from exc

        self._service = build("gmail", "v1", credentials=credentials)
        self._user_id = user_id

    @classmethod
    def from_config(cls, config: GmailDeliveryConfig) -> "GmailSender":
        """Build a Gmail sender from workflow delivery config and environment."""

        credentials = build_user_oauth_credentials(
            client_secrets_path=_optional_env_path(config.client_secrets_path_env),
            token_path=_optional_env_path(config.token_path_env),
            scopes=config.scopes,
        )
        return cls(credentials)

    def send_raw_message(self, message_text: str) -> GmailSendResult:
        """Send one complete RFC 822 message."""

        encoded = base64.urlsafe_b64encode(message_text.encode("utf-8")).decode("ascii")
        response = (
            self._service.users()
            .messages()
            .send(userId=self._user_id, body={"raw": encoded})
            .execute()
        )
        return GmailSendResult(message_id=response["id"], thread_id=response.get("threadId"))


def _optional_env_path(name: str) -> Path | None:
    value = os.getenv(name, "").strip()
    return Path(value) if value else None
