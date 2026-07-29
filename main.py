"""Synchronous local CLI for invoice processing."""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Sequence
from pathlib import Path

from rich.console import Console

from backend.app.bootstrap.invoice_runtime import build_invoice_processor
from backend.app.cli.renderers import PrettyCliRenderer
from backend.app.core.config import Settings, get_settings
from backend.app.ports.providers import ProviderConfigurationError
from backend.app.schemas.domain import ErrorBody, ErrorEnvelope, RunDetail, RunStatus
from backend.app.services.invoice_processing import (
    InvalidInvoiceInput,
    InvoiceProcessingService,
)

EXIT_INVALID_INPUT = 2
EXIT_CONFIGURATION_ERROR = 3
EXIT_WORKFLOW_FAILED = 5
EXIT_TIMEOUT = 6


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Process a local invoice through the multi-agent workflow.",
        epilog=(
            "Examples:\n"
            "  python main.py --invoice_path=data/invoices/invoice_1001.txt\n"
            "  python main.py --invoice-path=data/invoices/invoice_1001.txt "
            "--format json"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--invoice_path",
        "--invoice-path",
        dest="invoice_path",
        required=True,
        type=Path,
        help="Local PDF, TXT, JSON, CSV, or XML invoice.",
    )
    parser.add_argument("--timeout-seconds", type=int, default=300)
    parser.add_argument(
        "--format",
        choices=("pretty", "json"),
        default="pretty",
        help="Output format (default: pretty).",
    )
    parser.add_argument(
        "--show-events",
        action="store_true",
        help="Show every timeline event in pretty output.",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable terminal styling in pretty output.",
    )
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
        _print_error(
            "INVALID_INPUT",
            "Timeout must be a positive integer.",
            output_format=args.format,
            no_color=args.no_color,
        )
        return EXIT_INVALID_INPUT
    processor: InvoiceProcessingService | None = None
    try:
        processor = build_invoice_processor(settings or get_settings())
        detail = processor.process_path(
            args.invoice_path,
            origin="cli",
            timeout_seconds=args.timeout_seconds,
        )
    except InvalidInvoiceInput as exc:
        _print_error(
            "INVALID_INPUT",
            str(exc),
            output_format=args.format,
            no_color=args.no_color,
        )
        return EXIT_INVALID_INPUT
    except ProviderConfigurationError as exc:
        _print_error(
            "PROVIDER_NOT_CONFIGURED",
            str(exc),
            output_format=args.format,
            no_color=args.no_color,
        )
        return EXIT_CONFIGURATION_ERROR
    finally:
        if processor is not None:
            processor.close()
    _print_detail(
        detail,
        output_format=args.format,
        show_events=args.show_events,
        no_color=args.no_color,
    )
    if detail.status != RunStatus.FAILED:
        return 0
    if detail.error and detail.error.code == "WORKFLOW_TIMEOUT":
        return EXIT_TIMEOUT
    return EXIT_WORKFLOW_FAILED


def _print_detail(
    detail: RunDetail,
    *,
    output_format: str,
    show_events: bool,
    no_color: bool,
) -> None:
    if output_format == "json":
        print(detail.model_dump_json())
        return
    PrettyCliRenderer(_console(sys.stdout, no_color=no_color)).render_result(
        detail, show_events=show_events
    )


def _print_error(
    code: str,
    message: str,
    *,
    output_format: str,
    no_color: bool,
) -> None:
    envelope = ErrorEnvelope(error=ErrorBody(code=code, message=message))
    if output_format == "json":
        print(envelope.model_dump_json(), file=sys.stderr)
        return
    PrettyCliRenderer(_console(sys.stderr, no_color=no_color)).render_error(envelope)


def _console(stream, *, no_color: bool) -> Console:
    disable_styles = no_color or "NO_COLOR" in os.environ
    return Console(
        file=stream,
        highlight=False,
        color_system=None if disable_styles else "auto",
        no_color=disable_styles,
    )


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
