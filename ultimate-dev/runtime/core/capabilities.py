from dataclasses import dataclass, field
from typing import Any, Callable

from .contracts import validate_capability_id


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

    def __post_init__(self) -> None:
        validate_capability_id(self.name)
        if not isinstance(self.description, str) or not self.description.strip():
            raise ValueError("capability description is required")
        if not callable(self.execute):
            raise TypeError("capability execute must be callable")
        if not 0.0 <= float(self.risk) <= 1.0:
            raise ValueError("capability risk must be between 0 and 1")
        if not isinstance(self.effects, set):
            raise TypeError("capability effects must be a set")

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
    def __init__(self):
        self._items: dict[str, Capability] = {}

    def register(self, capability: Capability, *, replace: bool = False) -> Capability:
        if capability.name in self._items and not replace:
            raise ValueError(f"capability already registered: {capability.name}")
        self._items[capability.name] = capability
        return capability

    def get(self, name: str):
        validate_capability_id(name)
        return self._items.get(name)

    def discover(self, tags=None):
        tags = set(tags or [])
        return [capability for capability in self._items.values() if not tags or tags.intersection(capability.tags)]

    def jev_catalog(self):
        return [capability.jev_descriptor() for capability in self.discover() if capability.available]

    def catalog_descriptors(self):
        """Project registered capabilities into the canonical workflow catalog."""
        from .registry import CapabilityDescriptor

        return tuple(
            CapabilityDescriptor(
                id=capability.name,
                description=capability.description,
                effects=tuple(sorted(capability.effects)),
                available=capability.available,
                risk=capability.risk,
                reversible=capability.reversible,
                isolation=capability.isolation,
            )
            for capability in sorted(self.discover(), key=lambda item: item.name)
        )
