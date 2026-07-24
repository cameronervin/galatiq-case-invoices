"""Synchronous local CLI for invoice processing."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from backend.app.core.config import Settings, get_settings
from backend.app.infrastructure.llm.factory import ProviderConfigurationError
from backend.app.schemas.domain import ErrorBody, ErrorEnvelope, RunStatus
from backend.app.services.invoice_processing import (
    InvalidInvoiceInput,
    InvoiceProcessingService,
)

EXIT_INVALID_INPUT = 2
EXIT_CONFIGURATION_ERROR = 3
EXIT_WORKFLOW_FAILED = 5
EXIT_TIMEOUT = 6


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Process a local invoice.")
    parser.add_argument("--invoice_path", required=True, type=Path)
    parser.add_argument("--timeout-seconds", type=int, default=300)
    return parser


def run(
    argv: Sequence[str] | None = None,
    *,
    settings: Settings | None = None,
) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return int(exc.code)
    if args.timeout_seconds <= 0:
        _print_error("INVALID_INPUT", "Timeout must be a positive integer.")
        return EXIT_INVALID_INPUT
    processor: InvoiceProcessingService | None = None
    try:
        processor = InvoiceProcessingService(settings or get_settings())
        detail = processor.process_path(
            args.invoice_path,
            origin="cli",
            timeout_seconds=args.timeout_seconds,
        )
    except InvalidInvoiceInput as exc:
        _print_error("INVALID_INPUT", str(exc))
        return EXIT_INVALID_INPUT
    except ProviderConfigurationError as exc:
        _print_error("PROVIDER_NOT_CONFIGURED", str(exc))
        return EXIT_CONFIGURATION_ERROR
    finally:
        if processor is not None:
            processor.close()
    print(detail.model_dump_json())
    if detail.status != RunStatus.FAILED:
        return 0
    if detail.error and detail.error.code == "WORKFLOW_TIMEOUT":
        return EXIT_TIMEOUT
    return EXIT_WORKFLOW_FAILED


def _print_error(code: str, message: str) -> None:
    envelope = ErrorEnvelope(error=ErrorBody(code=code, message=message))
    print(envelope.model_dump_json(), file=sys.stderr)


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
