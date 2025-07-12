from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Optional

from .dataset import Dataset, Sample
from .solver import Solver
from .scorer import Score, Scorer
from .tool import Tool


@dataclass
class Task:
    dataset: Dataset
    solver: Solver
    scorer: Scorer
    metadata: Dict[str, Any]


def task(func: Callable) -> Callable:
    """Decorator for task factory functions."""
    return func

