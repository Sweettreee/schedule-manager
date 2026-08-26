"""Read message headers from the collection mailbox.

Only headers are fetched (`format="metadata"`). Message bodies are B2's problem, and not
pulling them here means no mail content passes through this block at all.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from googleapiclient.discovery import build

from schedule_manager.gmail.auth import get_credentials

_METADATA_HEADERS = ["From", "Subject"]


@dataclass(frozen=True)
class MessageHeader:
    """One message, reduced to what B1 prints.

    `received_at` is timezone-aware UTC. Conversion to KST happens at the presentation
    layer only (CLAUDE.md §4).
    """

    message_id: str
    received_at: datetime
    sender: str
    subject: str


def _to_header(payload: dict[str, Any]) -> MessageHeader:
    headers = {h["name"].lower(): h["value"] for h in payload.get("payload", {}).get("headers", [])}
    # internalDate is epoch milliseconds and is UTC by definition.
    received_at = datetime.fromtimestamp(int(payload["internalDate"]) / 1000, tz=UTC)
    return MessageHeader(
        message_id=payload["id"],
        received_at=received_at,
        sender=headers.get("from", "(unknown sender)"),
        subject=headers.get("subject", "(no subject)"),
    )


def list_recent(limit: int = 10) -> list[MessageHeader]:
    """Return the most recent `limit` messages, newest first."""
    service = build("gmail", "v1", credentials=get_credentials(), cache_discovery=False)
    messages = service.users().messages()

    listing = messages.list(userId="me", maxResults=limit).execute()

    headers: list[MessageHeader] = []
    for ref in listing.get("messages", []):
        detail = messages.get(
            userId="me",
            id=ref["id"],
            format="metadata",
            metadataHeaders=_METADATA_HEADERS,
        ).execute()
        headers.append(_to_header(detail))
    return headers
