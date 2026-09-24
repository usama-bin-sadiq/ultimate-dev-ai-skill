from dataclasses import dataclass, field
from typing import Callable, Any

@dataclass
class Capability:
    name: str
    description: str
    execute: Callable[..., Any]
    reversible: bool = True
    tags: set[str] = field(default_factory=set)
    available: bool = True
    isolation: str = "host_managed"
    risk: float = 0.0
    effects: set[str] = field(default_factory=set)

    def jev_descriptor(self) -> dict[str, Any]:
        """Return the language-neutral descriptor expected by JEV."""
        return {
            "id": self.name,
            "available": self.available,
            "reversible": self.reversible,
            "isolation": self.isolation,
            "risk": self.risk,
            "effects": sorted(self.effects),
        }

class CapabilityRegistry:
    def __init__(self): self._items = {}
    def register(self, capability: Capability): self._items[capability.name] = capability
    def get(self, name: str): return self._items.get(name)
    def discover(self, tags=None):
        tags=set(tags or [])
        return [c for c in self._items.values() if not tags or tags.intersection(c.tags)]
    def jev_catalog(self):
        return [c.jev_descriptor() for c in self.discover() if c.available]
