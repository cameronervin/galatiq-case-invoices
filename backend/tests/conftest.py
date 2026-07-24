import pytest

from backend.app.core.config import get_settings


@pytest.fixture(autouse=True)
def clear_cached_resources() -> None:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
