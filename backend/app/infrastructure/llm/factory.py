from backend.app.infrastructure.llm.base import LLMProvider
from backend.app.infrastructure.llm.providers import GrokProvider, OfflineProvider


class ProviderConfigurationError(RuntimeError):
    pass


class ProviderRegistry:
    def __init__(self, *, grok_api_key: str | None, grok_model: str) -> None:
        self.grok_api_key = grok_api_key
        self.grok_model = grok_model
        self._offline = OfflineProvider()

    def get(self, provider_name: str, model_name: str) -> LLMProvider:
        if provider_name == "offline":
            if model_name != self._offline.model_name:
                raise ProviderConfigurationError("Unknown offline model configuration.")
            return self._offline
        if provider_name == "grok":
            if not self.grok_api_key:
                raise ProviderConfigurationError(
                    "XAI_API_KEY is required when APP_LLM_PROVIDER=grok."
                )
            return GrokProvider(
                api_key=self.grok_api_key,
                model_name=model_name or self.grok_model,
            )
        raise ProviderConfigurationError(f"Unknown LLM provider: {provider_name}")


def get_llm_provider(settings: object) -> LLMProvider:
    provider_name = settings.llm_provider
    model_name = settings.llm_model
    registry = ProviderRegistry(
        grok_api_key=getattr(settings, "xai_api_key", None),
        grok_model=getattr(settings, "grok_model", "grok-4.5"),
    )
    return registry.get(provider_name, model_name)
