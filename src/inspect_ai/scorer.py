from dataclasses import dataclass
from typing import Any, Callable, Dict


@dataclass
class Score:
    value: float
    metadata: Dict[str, Any]


class Scorer:
    async def score(self, state, target: Any) -> Score:
        raise NotImplementedError


Target = Any


def scorer(*, metrics=None):
    def decorator(func: Callable) -> Callable:
        return func
    return decorator

