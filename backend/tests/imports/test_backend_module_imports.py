import importlib

import pytest

MODULES = [
    "main",
    "backend.app.main",
    "backend.app.agents.graph_provider",
    "backend.app.agents.builders.graphs_builder",
    "backend.app.agents.executors.invoice_pipeline",
    "backend.app.api.v1.router",
    "backend.app.core.config",
    "backend.app.infrastructure.db.session",
    "backend.app.infrastructure.llm.factory",
    "backend.app.repositories.base",
    "backend.app.schemas.run",
    "backend.app.services.agent_run_service",
    "backend.app.workers.app",
    "backend.app.workers.tasks",
]


@pytest.mark.parametrize("module_name", MODULES)
def test_backend_module_imports(module_name: str) -> None:
    assert importlib.import_module(module_name) is not None
