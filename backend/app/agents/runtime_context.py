from dataclasses import dataclass

from backend.app.core.config import Settings
from backend.app.infrastructure.llm import LLMProvider


@dataclass(frozen=True)
class AgentRuntimeContext:
    settings: Settings
    llm_provider: LLMProvider

