from collections.abc import Callable

from backend.app.schemas.invoice import InvoiceData, InvoiceItem
from backend.app.schemas.workflow import FindingSeverity, ValidationFinding

from .findings import blocking_finding

InventoryLookup = Callable[[str], tuple[str, int, bool] | None]


def inventory_findings(
    invoice: InvoiceData, lookup: InventoryLookup
) -> tuple[list[InvoiceItem], list[ValidationFinding]]:
    """Normalize inventory identities and validate aggregate stock availability."""
    findings: list[ValidationFinding] = []
    normalized: list[InvoiceItem] = []
    totals: dict[str, int] = {}
    stocks: dict[str, int] = {}
    lines: dict[str, list[int]] = {}
    resolutions: dict[str, tuple[str, int, bool] | None] = {}
    for item in invoice.items:
        if not item.source_name:
            normalized.append(item)
            continue
        lookup_key = " ".join(item.source_name.strip().lower().split())
        if lookup_key not in resolutions:
            resolutions[lookup_key] = lookup(item.source_name)
        resolved = resolutions[lookup_key]
        if resolved is None:
            findings.append(
                blocking_finding(
                    "UNKNOWN_ITEM",
                    f"items.{item.line_number - 1}.source_name",
                    "Item is not present in inventory.",
                    line=item.line_number,
                )
            )
            normalized.append(item)
            continue
        code, stock, used_alias = resolved
        normalized.append(item.model_copy(update={"normalized_item_code": code}))
        if used_alias:
            findings.append(
                ValidationFinding(
                    code="ITEM_ALIAS_NORMALIZATION",
                    severity=FindingSeverity.INFO,
                    field_path=f"items.{item.line_number - 1}.source_name",
                    item_line_number=item.line_number,
                    message="An exact configured item alias was normalized.",
                )
            )
        if item.quantity is not None and item.quantity > 0:
            totals[code] = totals.get(code, 0) + item.quantity
            stocks[code] = stock
            lines.setdefault(code, []).append(item.line_number)
    findings.extend(_stock_findings(totals, stocks, lines))
    return normalized, findings


def _stock_findings(
    totals: dict[str, int], stocks: dict[str, int], lines: dict[str, list[int]]
) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    for code, quantity in totals.items():
        stock = stocks[code]
        finding_code = None
        message = None
        if stock == 0:
            finding_code = "OUT_OF_STOCK"
            message = "Inventory stock is zero."
        elif quantity > stock:
            finding_code = "QUANTITY_EXCEEDS_STOCK"
            message = "Aggregated quantity exceeds inventory stock."
        if finding_code is not None and message is not None:
            findings.append(
                ValidationFinding(
                    code=finding_code,
                    severity=FindingSeverity.BLOCKING,
                    field_path="items",
                    item_line_number=lines[code][0],
                    message=message,
                    expected={"maximum_quantity": stock},
                    actual={"quantity": quantity},
                )
            )
    return findings
