from backend.app.schemas.workflow import FindingSeverity, ValidationFinding

_SEVERITY_ORDER = {
    FindingSeverity.BLOCKING: 0,
    FindingSeverity.WARNING: 1,
    FindingSeverity.INFO: 2,
}


def blocking_finding(
    code: str, field_path: str | None, message: str, *, line: int | None = None
) -> ValidationFinding:
    """Build a blocking validation finding with a consistent shape."""
    return ValidationFinding(
        code=code,
        severity=FindingSeverity.BLOCKING,
        field_path=field_path,
        item_line_number=line,
        message=message,
    )


def ordered_unique(
    findings: list[ValidationFinding],
) -> list[ValidationFinding]:
    """Order by severity and remove findings with the same stable identity."""
    ordered = sorted(
        findings,
        key=lambda finding: (
            _SEVERITY_ORDER[finding.severity],
            finding.code,
            finding.item_line_number or 0,
        ),
    )
    seen: set[tuple[str, str | None, int | None]] = set()
    result: list[ValidationFinding] = []
    for finding in ordered:
        key = (finding.code, finding.field_path, finding.item_line_number)
        if key not in seen:
            seen.add(key)
            result.append(finding)
    return result
