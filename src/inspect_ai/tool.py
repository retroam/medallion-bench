from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class Tool:
    func: Callable

    async def __call__(self, *args, **kwargs) -> Any:
        return await self.func(*args, **kwargs)


def tool(func: Callable) -> Callable:
    """Decorator turning a factory into a Tool-returning function."""

    def wrapper(*args, **kwargs) -> Tool:
        inner = func(*args, **kwargs)
        return Tool(func=inner)

    return wrapper

