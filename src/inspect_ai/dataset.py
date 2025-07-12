from dataclasses import dataclass
from typing import Any, Dict, Iterable, List


@dataclass
class Sample:
    id: str
    input: str
    target: str
    metadata: Dict[str, Any]


class Dataset:
    """Simple dataset container."""

    def __init__(self, samples: Iterable[Sample]):
        self.samples: List[Sample] = list(samples)

    def __iter__(self):
        return iter(self.samples)

