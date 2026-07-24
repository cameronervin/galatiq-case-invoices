from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from backend.app.schemas.domain import InvoiceItem, Money


def invoice_number(text: str) -> str | None:
    match = re.search(r"\bINV[\s-]?(\d{4})\b", text, re.IGNORECASE)
    if match:
        return f"INV-{match.group(1)}"
    match = re.search(r"(?im)^\s*Inv\s*#\s*:\s*(\d{4})\s*$", text)
    return f"INV-{match.group(1)}" if match else None


def vendor(text: str) -> str | None:
    match = re.search(r"(?im)^\s*(?:Vendor|Vndr|FROM)\s*:\s*([^\n]+)", text)
    return match.group(1).strip() if match else None


def labeled_date(text: str, labels: tuple[str, ...]) -> str | None:
    label_pattern = "|".join(re.escape(label) for label in labels)
    match = re.search(rf"(?im)^\s*(?:{label_pattern})\s*:\s*([^\n]+)", text)
    if not match:
        return None
    value = match.group(1).strip()
    for pattern in ("%Y-%m-%d", "%b %d %Y", "%B %d, %Y", "%d-%b-%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(value, pattern).date().isoformat()
        except ValueError:
            continue
    return None


def text_items(text: str, currency: str) -> list[InvoiceItem]:
    items: list[InvoiceItem] = []
    for line in text.splitlines():
        if "$" not in line and "€" not in line:
            continue
        if re.search(r"(?i)subtotal|tax|shipping|total amount|^\s*total\s*:", line):
            continue
        compact = line.strip().lstrip("-").strip()
        match = re.match(
            r"(?P<name>[A-Za-z][A-Za-z0-9 ]*?(?:\s*\([^)]*\))?)\s+"
            r"x(?P<qty>-?\d+)\s+[$€](?P<price>[\d,.]+)",
            compact,
            re.IGNORECASE,
        )
        if not match:
            match = re.match(
                r"(?P<name>[A-Za-z][A-Za-z0-9 ]*?(?:\s*\([^)]*\))?)\s+"
                r"(?:(?:qty\s*:?)\s*)?(?P<qty>-?\d+)\s+"
                r"(?:(?:unit\s+price\s*:?)|@)?\s*[$€](?P<price>[\d,.]+)",
                compact,
                re.IGNORECASE,
            )
        if not match:
            continue
        name = " ".join(match.group("name").split())
        if name.lower() in {"item", "description"}:
            continue
        quantity = int(match.group("qty"))
        price = Decimal(match.group("price").replace(",", ""))
        items.append(
            InvoiceItem(
                line_number=len(items) + 1,
                source_name=name,
                quantity=quantity,
                unit_price=Money(amount=price, currency=currency),
                line_total=Money(amount=price * quantity, currency=currency),
            )
        )
    if items:
        return items
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for index in range(len(lines) - 3):
        name, quantity_text, price_text, total_text = lines[index : index + 4]
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9 ]*(?:\([^)]*\))?", name):
            continue
        if not re.fullmatch(r"-?\d+", quantity_text):
            continue
        if not re.fullmatch(r"[$€][\d,.]+", price_text):
            continue
        if not re.fullmatch(r"[$€][\d,.]+", total_text):
            continue
        price = Decimal(price_text[1:].replace(",", ""))
        total = Decimal(total_text[1:].replace(",", ""))
        items.append(
            InvoiceItem(
                line_number=len(items) + 1,
                source_name=name,
                quantity=int(quantity_text),
                unit_price=Money(amount=price, currency=currency),
                line_total=Money(amount=total, currency=currency),
            )
        )
    return items


def labeled_money(text: str, label: str, currency: str) -> Money | None:
    match = re.search(rf"(?im)^\s*{label}\s*:\s*[$€]?(?P<amount>-?[\d,.]+)", text)
    if not match:
        return None
    return Money(
        amount=match.group("amount").replace(",", ""),
        currency=currency,
    )


def total_money(text: str, currency: str) -> Money | None:
    for label in ("TOTAL", "Total Amount", "Amt", "Grand Total"):
        money = labeled_money(text, label, currency)
        if money is not None:
            return money
    return None


def payment_terms(text: str) -> str | None:
    match = re.search(
        r"(?im)^\s*(?:Payment Terms|Pymnt Terms|Terms)\s*:\s*([^\n]+)", text
    )
    return match.group(1).strip() if match else None
