from __future__ import annotations

import ast
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
BACKEND_SOURCE = PROJECT_ROOT / "backend" / "app"
SQLITE_ALLOWLIST = {
    BACKEND_SOURCE / "infrastructure" / "graph" / "provider.py",
    BACKEND_SOURCE / "infrastructure" / "db" / "session.py",
}


def test_first_party_backend_has_no_raw_sql_escape_hatches() -> None:
    violations: list[str] = []
    for path in BACKEND_SOURCE.rglob("*.py"):
        tree = ast.parse(path.read_text(), filename=str(path))
        relative = path.relative_to(PROJECT_ROOT)
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)) and _imports_sqlite3(
                node
            ):
                if path not in SQLITE_ALLOWLIST:
                    violations.append(f"{relative}:{node.lineno}: sqlite3 import")
            if isinstance(node, ast.Name) and node.id == "INITIAL_SCHEMA":
                violations.append(f"{relative}:{node.lineno}: INITIAL_SCHEMA")
            if not isinstance(node, ast.Call):
                continue
            name = _call_name(node.func)
            if name in {"text", "exec_driver_sql", "executescript", "executemany"}:
                violations.append(f"{relative}:{node.lineno}: {name}()")
            if (
                name == "execute"
                and node.args
                and isinstance(node.args[0], ast.Constant)
            ):
                if isinstance(node.args[0].value, str):
                    violations.append(f"{relative}:{node.lineno}: raw execute string")
            if name == "execute" and isinstance(node.func, ast.Attribute):
                owner = _call_name(node.func.value)
                if owner in {"connection", "cursor"}:
                    violations.append(f"{relative}:{node.lineno}: {owner}.execute()")

    assert violations == []


def _imports_sqlite3(node: ast.Import | ast.ImportFrom) -> bool:
    if isinstance(node, ast.Import):
        return any(alias.name == "sqlite3" for alias in node.names)
    return node.module == "sqlite3"


def _call_name(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None
