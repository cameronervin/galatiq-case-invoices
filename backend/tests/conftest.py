import pytest

from backend.app.agents.graph_provider import clear_graph_provider_cache
from backend.app.core.config import get_settings


@pytest.fixture(autouse=True)
def clear_cached_resources() -> None:
    get_settings.cache_clear()
    clear_graph_provider_cache()
    yield
    clear_graph_provider_cache()
    get_settings.cache_clear()
