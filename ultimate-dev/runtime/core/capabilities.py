import math
from dataclasses import dataclass, field
from typing import Any, Callable

from .contracts import CAPABILITY_EFFECTS, validate_capability_id


@dataclass(frozen=True)
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
        if isinstance(self.risk, bool) or not isinstance(self.risk, (int, float)):
            raise ValueError("capability risk must be a finite number between 0 and 1")
        if not math.isfinite(float(self.risk)) or not 0.0 <= float(self.risk) <= 1.0:
            raise ValueError("capability risk must be a finite number between 0 and 1")
        object.__setattr__(self, "risk", float(self.risk))
        if not isinstance(self.effects, (set, frozenset)) or any(not isinstance(effect, str) or not effect for effect in self.effects):
            raise TypeError("capability effects must be a set of non-empty strings")
        effects = frozenset(self.effects)
        unknown_effects = effects - CAPABILITY_EFFECTS
        if unknown_effects:
            raise ValueError(f"capability effects contains unknown labels: {', '.join(sorted(unknown_effects))}")
        object.__setattr__(self, "effects", effects)
        if not isinstance(self.tags, (set, frozenset)) or any(not isinstance(tag, str) or not tag for tag in self.tags):
            raise TypeError("capability tags must be a set of non-empty strings")
        object.__setattr__(self, "tags", frozenset(self.tags))
        if not isinstance(self.available, bool) or not isinstance(self.reversible, bool):
            raise TypeError("capability availability/reversibility must be boolean")
        if not isinstance(self.isolation, str) or not self.isolation.strip():
            raise ValueError("capability isolation must be a non-empty string")

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
        if not isinstance(capability, Capability):
            raise TypeError("capability must be a Capability")
        if capability.name in self._items and not replace:
            raise ValueError(f"capability already registered: {capability.name}")
        self._items[capability.name] = capability
        return capability

    def get(self, name: str):
        validate_capability_id(name)
        return self._items.get(name)

    def discover(self, tags=None):
        if tags is None:
            tags = set()
        elif isinstance(tags, str):
            tags = {tags}
        else:
            try:
                tags = set(tags)
            except TypeError as exc:
                raise TypeError("capability tags must be an iterable of strings") from exc
        if any(not isinstance(tag, str) or not tag for tag in tags):
            raise ValueError("capability tags must contain non-empty strings")
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
