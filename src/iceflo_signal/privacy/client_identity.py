"""Client identity helpers that preserve uniqueness without exposing names."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ClientIdentity:
    """Privacy-safe client identity values for EDW and presentation layers."""

    client_key: str
    client_display_name: str


class ClientIdentityTransformer:
    """Create stable internal keys and obfuscated display names for clients."""

    def __init__(self, namespace: str) -> None:
        self._namespace = namespace

    def transform_name(self, source_name: str) -> ClientIdentity:
        """Return a stable key and two-letter first/last display name."""

        normalized_name = _normalize_name(source_name)
        return ClientIdentity(
            client_key=self._hash_identity(normalized_name),
            client_display_name=_display_name(normalized_name),
        )

    def _hash_identity(self, normalized_name: str) -> str:
        payload = f"{self._namespace}:{normalized_name}".encode("utf-8")
        return hashlib.sha256(payload).hexdigest()


def _normalize_name(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip()).casefold()


def _display_name(normalized_name: str) -> str:
    parts = [part for part in re.split(r"\s+", normalized_name) if part]
    if not parts:
        return ""

    first = _first_two_letters(parts[0])
    last = _first_two_letters(parts[-1]) if len(parts) > 1 else ""
    return " ".join(part for part in (_title_token(first), _title_token(last)) if part)


def _first_two_letters(value: str) -> str:
    letters = [character for character in value if character.isalpha()]
    return "".join(letters[:2])


def _title_token(value: str) -> str:
    if not value:
        return ""
    return value[0].upper() + value[1:].lower()
