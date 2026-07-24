import pytest

from backend.app.infrastructure.llm.factory import ProviderRegistry
from backend.app.infrastructure.llm.offline import OfflineProvider
from backend.app.ports.providers import ProviderConfigurationError


def test_registry_requires_key_only_for_grok() -> None:
    registry = ProviderRegistry(grok_api_key=None, grok_model="grok-4.5")

    assert isinstance(registry.get("offline", "deterministic-v1"), OfflineProvider)
    with pytest.raises(ProviderConfigurationError):
        registry.get("grok", "grok-4.5")


def test_registry_dispatches_registered_factory_and_closes_by_capability() -> None:
    created: list[object] = []

    class CustomProvider:
        provider_name = "custom"

        def __init__(self, model_name: str) -> None:
            self.model_name = model_name
            self.close_calls = 0
            created.append(self)

        def close(self) -> None:
            self.close_calls += 1

    registry = ProviderRegistry(
        grok_api_key=None,
        grok_model="grok-4.5",
        provider_factories={"custom": CustomProvider},
    )

    first = registry.get("custom", "custom-v1")
    again = registry.get("custom", "custom-v1")
    registry.close()
    registry.close()

    assert first is again
    assert created == [first]
    assert first.close_calls == 1


def test_registry_can_replace_factory_before_provider_is_resolved() -> None:
    replacement = OfflineProvider()
    registry = ProviderRegistry(grok_api_key=None, grok_model="grok-4.5")
    registry.register_factory("offline", lambda _model: replacement, replace=True)

    resolved = registry.get("offline", "deterministic-v1")

    assert resolved is replacement


def test_registry_caches_provider_per_profile_and_closes_once(monkeypatch) -> None:
    created: list[object] = []

    class FakeProvider:
        provider_name = "grok"

        def __init__(self, *, api_key: str, model_name: str) -> None:
            del api_key
            self.model_name = model_name
            self.close_calls = 0
            created.append(self)

        def close(self) -> None:
            self.close_calls += 1

    monkeypatch.setattr(
        "backend.app.infrastructure.llm.factory.GrokProvider", FakeProvider
    )
    registry = ProviderRegistry(grok_api_key="test-key", grok_model="grok-4.5")

    first = registry.get("grok", "grok-4.5")
    again = registry.get("grok", "grok-4.5")
    other = registry.get("grok", "grok-4-fast")
    registry.close()
    registry.close()

    assert first is again
    assert other is not first
    assert len(created) == 2
    assert [provider.close_calls for provider in created] == [1, 1]
    with pytest.raises(ProviderConfigurationError, match="closed"):
        registry.get("grok", "grok-after-close")
