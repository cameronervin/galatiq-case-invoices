from collections.abc import Callable, Mapping

from backend.app.infrastructure.llm.live import GrokProvider
from backend.app.infrastructure.llm.offline import OfflineProvider
from backend.app.ports.providers import (
    LLMProvider,
    ProviderConfigurationError,
)

ProviderFactory = Callable[[str], LLMProvider]


class ProviderRegistry:
    def __init__(
        self,
        *,
        grok_api_key: str | None,
        grok_model: str,
        provider_factories: Mapping[str, ProviderFactory] | None = None,
    ) -> None:
        self.grok_api_key = grok_api_key
        self.grok_model = grok_model
        self._offline = OfflineProvider()
        factories: dict[str, ProviderFactory] = {
            "offline": self._create_offline,
            "grok": self._create_grok,
        }
        factories.update(provider_factories or {})
        self._factories = factories
        self._providers: dict[tuple[str, str], LLMProvider] = {}
        self._closed = False

    def get(self, provider_name: str, model_name: str) -> LLMProvider:
        if self._closed:
            raise ProviderConfigurationError("LLM provider registry is closed.")
        factory = self._factories.get(provider_name)
        if factory is None:
            raise ProviderConfigurationError(f"Unknown LLM provider: {provider_name}")
        resolved_model = model_name or (
            self.grok_model if provider_name == "grok" else model_name
        )
        profile = (provider_name, resolved_model)
        provider = self._providers.get(profile)
        if provider is None:
            provider = factory(resolved_model)
            self._providers[profile] = provider
        return provider

    def register_factory(
        self,
        provider_name: str,
        factory: ProviderFactory,
        *,
        replace: bool = False,
    ) -> None:
        if self._closed:
            raise ProviderConfigurationError("LLM provider registry is closed.")
        if provider_name in self._factories and not replace:
            raise ProviderConfigurationError(
                f"LLM provider factory is already registered: {provider_name}"
            )
        if any(profile[0] == provider_name for profile in self._providers):
            raise ProviderConfigurationError(
                f"Initialized provider factory cannot be replaced: {provider_name}"
            )
        self._factories[provider_name] = factory

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        seen: set[int] = set()
        for provider in self._providers.values():
            if id(provider) in seen:
                continue
            seen.add(id(provider))
            close = getattr(provider, "close", None)
            if callable(close):
                close()

    def _create_offline(self, model_name: str) -> LLMProvider:
        if model_name != self._offline.model_name:
            raise ProviderConfigurationError("Unknown offline model configuration.")
        return self._offline

    def _create_grok(self, model_name: str) -> LLMProvider:
        if not self.grok_api_key:
            raise ProviderConfigurationError(
                "XAI_API_KEY is required when APP_LLM_PROVIDER=grok."
            )
        return GrokProvider(api_key=self.grok_api_key, model_name=model_name)
