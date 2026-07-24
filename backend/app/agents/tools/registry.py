from collections.abc import Callable


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Callable[..., object]] = {}

    def register(self, name: str, tool: Callable[..., object]) -> None:
        if name in self._tools:
            raise ValueError(f"Tool already registered: {name}")
        self._tools[name] = tool

    def get(self, name: str) -> Callable[..., object]:
        try:
            return self._tools[name]
        except KeyError as exc:
            raise KeyError(f"Unknown tool: {name}") from exc

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._tools))

