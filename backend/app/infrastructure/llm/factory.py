from dataclasses import dataclass

from backend.app.core.config import Settings


@dataclass(frozen=True)
class UnconfiguredLLMProvider:
    provider_name: str = "unconfigured"

    async def complete(self, *, system_prompt: str, user_prompt: str) -> str:
        raise RuntimeError("No LLM provider has been configured")


def get_llm_provider(settings: Settings) -> UnconfiguredLLMProvider:
    """Return the scaffold provider until a live adapter is implemented."""
    return UnconfiguredLLMProvider(provider_name=settings.llm_provider)

