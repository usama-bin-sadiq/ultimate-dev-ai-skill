from dataclasses import dataclass, field
from typing import Callable, Any

@dataclass
class Capability:
    name: str
    description: str
    execute: Callable[..., Any]
    reversible: bool = True
    tags: set[str] = field(default_factory=set)

class CapabilityRegistry:
    def __init__(self): self._items = {}
    def register(self, capability: Capability): self._items[capability.name] = capability
    def get(self, name: str): return self._items.get(name)
    def discover(self, tags=None):
        tags=set(tags or [])
        return [c for c in self._items.values() if not tags or tags.intersection(c.tags)]
