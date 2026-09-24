from __future__ import annotations

from .contracts import CAPABILITY_EFFECTS, normalize_effects, validate_capability_id

DESTRUCTIVE_ACTIONS = frozenset({
    "delete_data",
    "drop_database",
    "force_push",
    "destroy_infrastructure",
    "rotate_credentials",
    "publish_release",
    "production_deploy",
})
DESTRUCTIVE_EFFECTS = frozenset({
    "delete",
    "destroy",
    "force_push",
    "production",
    "rotate_credentials",
    "irreversible",
})


class Policy:
    """Small deterministic policy helper used at the runtime boundary."""

    def __init__(
        self,
        confirmation_required=None,
        *,
        denied_capabilities=(),
        denied_effects=(),
    ):
        if confirmation_required is None:
            values = DESTRUCTIVE_ACTIONS
        elif isinstance(confirmation_required, str):
            values = {confirmation_required}
        else:
            try:
                values = set(confirmation_required)
            except TypeError as exc:
                raise ValueError("confirmation_required must be an iterable of strings") from exc
        if any(not isinstance(value, str) or not value for value in values):
            raise ValueError("confirmation_required must contain non-empty strings")
        self.confirmation_required = frozenset(values)
        try:
            self.denied_capabilities = frozenset(denied_capabilities or ())
            self.denied_effects = frozenset(denied_effects or ())
        except TypeError as exc:
            raise ValueError("policy denials must be iterable") from exc
        for capability_id in self.denied_capabilities:
            validate_capability_id(capability_id)
        unknown_effects = self.denied_effects - CAPABILITY_EFFECTS
        if unknown_effects or any(not isinstance(value, str) or not value for value in self.denied_effects):
            raise ValueError("denied_effects contains an invalid effect")

    @classmethod
    def secure_defaults(cls) -> "Policy":
        """Return a side-effect-confirming policy for JEV-gated runtimes."""
        return cls(
            confirmation_required=set(DESTRUCTIVE_ACTIONS) | {"execute", "write", "network", "communicate"},
        )

    def check(self, action: str, confirmed: bool = False) -> dict:
        if not isinstance(action, str) or not action:
            raise ValueError("policy action must be a non-empty string")
        if not isinstance(confirmed, bool):
            raise ValueError("policy confirmation must be boolean")
        if action in self.denied_capabilities or action in self.denied_effects:
            return {
                "allowed": False,
                "confirmation_required": False,
                "reason": "policy_denied",
            }
        required = action in self.confirmation_required
        return {
            "allowed": (not required) or confirmed,
            "confirmation_required": required,
            "reason": "confirmation_required" if required and not confirmed else None,
        }

    def check_capability(
        self,
        capability_id: str,
        effects: set[str] | frozenset[str] | list[str] | tuple[str, ...] = (),
        confirmed: bool = False,
        *,
        irreversible: bool = False,
    ) -> dict:
        """Check a canonical capability and its declared side effects."""
        validate_capability_id(capability_id)
        if not isinstance(confirmed, bool) or not isinstance(irreversible, bool):
            raise ValueError("policy confirmation and irreversible must be boolean")
        effect_set = set(normalize_effects(effects))
        denied = capability_id in self.denied_capabilities or bool(effect_set.intersection(self.denied_effects))
        required = (
            capability_id in self.confirmation_required
            or bool(effect_set.intersection(self.confirmation_required))
            or bool(effect_set.intersection(DESTRUCTIVE_EFFECTS))
            or irreversible
        )
        return {
            "allowed": (not denied) and ((not required) or confirmed),
            "confirmation_required": required,
            "denied": denied,
            "capability_id": capability_id,
            "effects": sorted(effect_set),
            "reason": "policy_denied" if denied else ("confirmation_required" if required and not confirmed else None),
        }
