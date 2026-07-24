"""Command-line entrypoint for submitting invoice-processing runs."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from pydantic import ValidationError

from backend.app.core.config import get_settings
from backend.app.services.agent_run_service import (
    AgentRunDispatchError,
    AgentRunDispatchService,
)

SUPPORTED_INVOICE_SUFFIXES = {".csv", ".json", ".pdf", ".txt", ".xml"}
EXIT_INVALID_INPUT = 2
EXIT_CONFIGURATION_ERROR = 3
EXIT_DISPATCH_ERROR = 4


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Queue an invoice for asynchronous agent processing."
    )
    parser.add_argument(
        "--invoice_path",
        required=True,
        type=Path,
        help="Path to a PDF, text, JSON, CSV, or XML invoice.",
    )
    return parser


def validate_invoice_path(path: Path) -> Path:
    resolved_path = path.expanduser().resolve()
    if not resolved_path.is_file():
        raise ValueError(f"Invoice file does not exist: {path}")
    if resolved_path.suffix.lower() not in SUPPORTED_INVOICE_SUFFIXES:
        supported = ", ".join(sorted(SUPPORTED_INVOICE_SUFFIXES))
        raise ValueError(
            f"Unsupported invoice type '{resolved_path.suffix or '<none>'}'. "
            f"Supported types: {supported}"
        )
    return resolved_path


def run(
    argv: Sequence[str] | None = None,
    *,
    dispatch_service: AgentRunDispatchService | None = None,
) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        invoice_path = validate_invoice_path(args.invoice_path)
    except ValueError as exc:
        _print_error("invalid_input", str(exc))
        return EXIT_INVALID_INPUT

    try:
        settings = get_settings()
    except ValidationError as exc:
        _print_error("configuration_error", str(exc))
        return EXIT_CONFIGURATION_ERROR

    service = dispatch_service or AgentRunDispatchService(settings=settings)
    try:
        queued_run = service.enqueue(invoice_path)
    except AgentRunDispatchError as exc:
        _print_error("dispatch_error", str(exc))
        return EXIT_DISPATCH_ERROR

    print(json.dumps(queued_run.model_dump(mode="json"), sort_keys=True))
    return 0


def _print_error(code: str, message: str) -> None:
    payload = json.dumps({"error": code, "message": message}, sort_keys=True)
    print(payload, file=sys.stderr)


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
