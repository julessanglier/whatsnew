from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TrendingItem:
    title: str
    url: str
    description: Optional[str] = None
    language: Optional[str] = None
    stars: Optional[int] = None
    extra: dict = field(default_factory=dict)


class BaseSource(ABC):
    name: str = "unnamed"
    enabled: bool = True

    @abstractmethod
    def fetch(self) -> list[TrendingItem]: ...
