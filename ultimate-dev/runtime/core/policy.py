from __future__ import annotations

from .contracts import validate_capability_id

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
            values = set(confirmation_required)
        self.confirmation_required = set(values)
        self.denied_capabilities = set(denied_capabilities or ())
        self.denied_effects = set(denied_effects or ())
        for capability_id in self.denied_capabilities:
            validate_capability_id(capability_id)

    def check(self, action: str, confirmed: bool = False) -> dict:
        if not isinstance(action, str) or not action:
            raise ValueError("policy action must be a non-empty string")
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
        if isinstance(effects, str):
            effect_set = {effects}
        else:
            effect_set = {str(effect) for effect in effects}
        denied = capability_id in self.denied_capabilities or bool(effect_set.intersection(self.denied_effects))
        required = (
            capability_id in self.confirmation_required
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
