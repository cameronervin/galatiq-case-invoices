import pytest

from backend.tests.architecture.support import APP_ROOT, backend_imports


@pytest.mark.parametrize(
    ("layer", "forbidden_layers"),
    [
        (
            "core",
            {
                "agents",
                "api",
                "bootstrap",
                "domain",
                "infrastructure",
                "services",
                "workers",
            },
        ),
        (
            "domain",
            {"agents", "api", "bootstrap", "infrastructure", "services", "workers"},
        ),
        (
            "ports",
            {"agents", "api", "bootstrap", "infrastructure", "services", "workers"},
        ),
        ("agents", {"api", "bootstrap", "infrastructure", "services", "workers"}),
        ("services", {"api", "bootstrap", "infrastructure", "workers"}),
        ("infrastructure", {"api", "bootstrap", "services", "workers"}),
    ],
)
def test_layers_only_depend_inward(layer: str, forbidden_layers: set[str]) -> None:
    violations: list[str] = []
    for path in (APP_ROOT / layer).rglob("*.py"):
        for imported in backend_imports(path):
            parts = imported.split(".")
            if len(parts) > 3 and parts[3] in forbidden_layers:
                violations.append(f"{path.relative_to(APP_ROOT)} imports {imported}")
    assert violations == []


def test_focused_schema_modules_do_not_depend_on_compatibility_exports() -> None:
    schema_package = APP_ROOT / "schemas"
    for module_name in {
        "errors.py",
        "invoice.py",
        "payment.py",
        "review.py",
        "runs.py",
        "workflow.py",
    }:
        assert "backend.app.schemas.domain" not in backend_imports(
            schema_package / module_name
        )
