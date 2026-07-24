import pytest

from backend.app.agents.graph_provider import clear_graph_provider_cache
from backend.app.core.config import get_settings
from backend.app.workers import app as worker_app


@pytest.fixture(autouse=True)
def clear_cached_resources() -> None:
    get_settings.cache_clear()
    clear_graph_provider_cache()
    worker_app.teardown_worker_resources()
    yield
    worker_app.teardown_worker_resources()
    clear_graph_provider_cache()
    get_settings.cache_clear()

