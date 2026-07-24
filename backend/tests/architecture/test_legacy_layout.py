from pathlib import Path

import pytest

from backend.tests.architecture.support import APP_ROOT


@pytest.mark.parametrize(
    "relative_path",
    [
        "agents/graph_provider.py",
        "agents/nodes/workflow.py",
        "agents/tools",
        "infrastructure/llm/base.py",
        "infrastructure/llm/errors.py",
        "infrastructure/llm/providers.py",
        "models",
        "repositories",
        "services/agent_run_service.py",
        "services/application.py",
        "services/invoice_runtime.py",
        "services/invoice_validation.py",
    ],
)
def test_legacy_layer_locations_are_empty(relative_path: str) -> None:
    path = APP_ROOT / relative_path
    if path.is_dir():
        assert _python_files(path) == []
    else:
        assert not path.exists()


def _python_files(path: Path) -> list[Path]:
    return list(path.rglob("*.py"))
