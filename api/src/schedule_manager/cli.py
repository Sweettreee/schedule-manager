"""Command line entry point.

B1's visible result: message subjects from the collection account print in the terminal.
"""

from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Sequence

from schedule_manager.config import KST
from schedule_manager.gmail.auth import MissingRefreshTokenError
from schedule_manager.gmail.client import list_recent

logger = logging.getLogger(__name__)


def _truncate(value: str, width: int) -> str:
    collapsed = " ".join(value.split())
    if len(collapsed) <= width:
        return collapsed
    return collapsed[: width - 1] + "…"


def _cmd_list(limit: int) -> int:
    messages = list_recent(limit)
    if not messages:
        print("no messages in the mailbox")
        return 0

    for message in messages:
        # Stored UTC, displayed KST — CLAUDE.md §4.
        when = message.received_at.astimezone(KST).strftime("%Y-%m-%d %H:%M")
        print(f"{when}  {_truncate(message.sender, 32):<32}  {_truncate(message.subject, 60)}")

    print(f"\n{len(messages)} message(s), times in KST")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="schedule-manager",
        description="Schedule Manager collector (B1: read the collection mailbox)",
    )
    subcommands = parser.add_subparsers(dest="command", required=True)

    list_parser = subcommands.add_parser("list", help="print the most recent messages")
    list_parser.add_argument("--limit", type=int, default=10, help="how many messages (default 10)")

    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    try:
        if args.command == "list":
            return _cmd_list(args.limit)
    except MissingRefreshTokenError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    parser.error(f"unknown command {args.command!r}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
