from typing import Protocol


class LLMProvider(Protocol):
    provider_name: str

    async def complete(self, *, system_prompt: str, user_prompt: str) -> str: ...

