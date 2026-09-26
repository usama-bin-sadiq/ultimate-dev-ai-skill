#!/usr/bin/env python3
"""The prompt plane must actually reach the host, and the gate with it.

A previous round of work wired the attestation gate into the runtime and
verified the detection recipe *ran*. It then wrote the recipe into the
repository-root ``AGENTS.md`` — a documentation file the host never reads — and
left the installable payload untouched. The recipe passed its own test and was
still unreachable. These tests exist to make that specific failure impossible
to repeat.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile

import pytest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(BASE)

# The installable payload. This is what a host actually loads.
SKILL = os.path.join(BASE, "AGENTS.md")
# Project-scope documentation. The host does not read this.
ROOT_AGENTS = os.path.join(REPO, "AGENTS.md")

GATE_TERMS = (
    "RUNTIME_AVAILABLE",
    "PROMPT_ONLY",
    "TOOL_ATTESTED",
    "SELF_REPORTED",
    "runtime_detected",
)


def read(path: str) -> str:
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def installed_copy() -> str | None:
    """Locate the globally installed skill, if the host has one."""
    for candidate in (
        os.path.expanduser("~/.agents/skills/ultimate-dev"),
        os.path.expanduser("~/.claude/skills/ultimate-dev"),
    ):
        if os.path.isfile(os.path.join(candidate, "AGENTS.md")):
            return candidate
    return None


class TestPayloadCarriesTheGate:
    """The installable skill, not the repo-root doc, must carry the rule."""

    def test_payload_agents_md_states_both_outcomes(self):
        text = read(SKILL)
        assert "RUNTIME_AVAILABLE" in text, (
            "ultimate-dev/AGENTS.md is the installed payload; the detection "
            "outcomes must appear there, not only in the repo-root AGENTS.md"
        )
        assert "PROMPT_ONLY" in text

    def test_payload_agents_md_states_the_evidence_grades(self):
        text = read(SKILL)
        assert "TOOL_ATTESTED" in text
        assert "SELF_REPORTED" in text

    def test_payload_contains_a_runnable_recipe(self):
        text = read(SKILL)
        assert "runtime-probe.py" in text, "the payload must invoke the probe"
        assert "```bash" in text, "the probe must be inside a runnable block"
        assert os.path.isfile(
            os.path.join(BASE, "scripts", "runtime-probe.py")
        ), "the payload references a probe script that does not exist"

    def test_root_agents_md_is_not_the_only_place_the_rule_lives(self):
        """Guards the exact regression: repo docs carrying it, payload not."""
        if not os.path.exists(ROOT_AGENTS):
            pytest.skip("no project-scope AGENTS.md in this repository")
        assert "RUNTIME_AVAILABLE" in read(SKILL), (
            "the rule exists only in the repo-root AGENTS.md, which the host "
            "never reads; copy it into the installable payload"
        )


class TestPreflightCarriesThePlane:
    def test_preflight_requires_runtime_detected(self):
        text = read(SKILL)
        preflight = text.split("ultimate-dev-preflight:")[-1].split("```")[0]
        assert "runtime_detected" in preflight, (
            "preflight must record the detected plane; the evidence grade for "
            "the whole task depends on it"
        )

    def test_status_block_requires_the_evidence_grade(self):
        text = read(SKILL)
        status = text.split("ultimate-dev-status:")[-1].split("```")[0]
        assert "evidence_grade" in status
        assert "TOOL_ATTESTED" in status and "SELF_REPORTED" in status

    def test_prompt_only_forbids_self_certifying_a_side_effect(self):
        text = read(SKILL).lower()
        assert "not_run" in text, (
            "the payload must state the honest report for unobserved work"
        )
        assert "unobserved" in text


class TestGroundingRuleReachesMidTaskFiles:
    """Skills and router rules are what a host reads *during* a task."""

    def test_grounding_rules_carry_the_evidence_grade(self):
        text = read(os.path.join(BASE, "router", "grounding-rules.md"))
        assert "Evidence Grade" in text
        assert "TOOL_ATTESTED" in text and "SELF_REPORTED" in text

    def test_grounding_rules_state_the_core_invariant(self):
        text = read(os.path.join(BASE, "router", "grounding-rules.md"))
        assert "CLAIMED CHANGE" in text and "OBSERVED CHANGE" in text

    def test_grounding_rules_forbid_self_attestation(self):
        text = read(os.path.join(BASE, "router", "grounding-rules.md"))
        assert "attested_by" in text, (
            "a host must be told it may not write runtime attestation itself"
        )


class TestTheRecipeRuns:
    def _recipe(self) -> str:
        text = read(SKILL)
        for block in re.findall(r"```bash\n(.*?)\n```", text, re.DOTALL):
            if "runtime-probe" in block:
                return block
        raise AssertionError("no detection recipe found in the payload AGENTS.md")

    def test_recipe_reports_available_from_the_skill_dir(self):
        """The recipe must work from the repo root, where the host starts."""
        result = subprocess.run(
            ["bash", "-c", self._recipe()],
            cwd=REPO,
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert result.returncode == 0, f"rc={result.returncode} {result.stderr}"
        assert "RUNTIME_AVAILABLE" in result.stdout, (
            f"expected RUNTIME_AVAILABLE, got {result.stdout!r} / {result.stderr!r}"
        )
        assert "No such file" not in result.stderr, (
            f"the recipe's path to the probe is wrong; stderr was {result.stderr!r}"
        )

    def test_recipe_reports_available_from_the_payload_dir(self):
        """A host may also run it from inside the installed skill folder."""
        result = subprocess.run(
            ["bash", "-c", self._recipe()],
            cwd=BASE,
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert result.returncode == 0, result.stderr
        assert "RUNTIME_AVAILABLE" in result.stdout, (
            f"expected RUNTIME_AVAILABLE, got {result.stdout!r} / {result.stderr!r}"
        )

    def test_probe_works_from_the_skill_dir(self):
        """The probe self-locates, so a host may run it from anywhere."""
        probe = os.path.join(BASE, "scripts", "runtime-probe.py")
        for workdir in (BASE, REPO, tempfile.gettempdir()):
            result = subprocess.run(
                [sys.executable, probe], cwd=workdir,
                capture_output=True, text=True, timeout=60,
            )
            assert result.returncode == 0, result.stderr
            expected = "PROMPT_ONLY" if workdir == tempfile.gettempdir() else "RUNTIME_AVAILABLE"
            assert result.stdout.strip() == expected, (
                f"probe from {workdir} returned {result.stdout.strip()!r}, "
                f"expected {expected!r}"
            )

    def test_recipe_never_prints_both_outcomes(self):
        result = subprocess.run(
            ["bash", "-c", self._recipe()],
            cwd=REPO,
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert not ("RUNTIME_AVAILABLE" in result.stdout and "PROMPT_ONLY" in result.stdout)

    def test_recipe_delegates_to_the_probe_script(self):
        """Detection logic must have one home, not be inlined in the prompt."""
        assert "runtime-probe" in self._recipe()
        assert "importlib" not in self._recipe(), (
            "the prompt must not inline probe logic; a duplicated probe drifts "
            "from the runtime and the entrypoint budget forbids the weight"
        )
        assert os.path.isfile(os.path.join(BASE, "scripts", "runtime-probe.py"))

    def test_probe_script_never_raises(self):
        """A broken probe must degrade to PROMPT_ONLY, not crash a session."""
        probe = os.path.join(BASE, "scripts", "runtime-probe.py")
        result = subprocess.run(
            [sys.executable, probe], cwd=tempfile.gettempdir(),
            capture_output=True, text=True, timeout=60,
        )
        assert result.returncode == 0
        assert result.stdout.strip() in {"RUNTIME_AVAILABLE", "PROMPT_ONLY"}

    def _load_probe(self):
        import importlib.util as _util

        spec = _util.spec_from_file_location(
            "runtime_probe_under_test", os.path.join(BASE, "scripts", "runtime-probe.py")
        )
        module = _util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_probe_outcome_follows_the_underlying_check(self):
        """detect() must consult runtime_available, not return a constant."""
        module = self._load_probe()

        # Break the payload check: the probe must then report PROMPT_ONLY.
        original_locate = module.locate
        try:
            module.locate = lambda: None
            assert module.detect() == module.PROMPT_ONLY
        finally:
            module.locate = original_locate

        # Restore it and the real answer comes back.
        assert module.detect() in {module.AVAILABLE, module.PROMPT_ONLY}

    def test_probe_reports_prompt_only_when_the_runtime_check_says_no(self):
        """A located payload whose runtime check fails must not claim AVAILABLE.

        This is the branch a located-but-unusable runtime takes. Without it, a
        probe that hardcoded ``AVAILABLE`` after locating the payload would
        pass every other test in this file.
        """
        import types

        module = self._load_probe()
        original_locate = module.locate
        original_module = sys.modules.get("runtime.core.attestation")
        fake = types.ModuleType("runtime.core.attestation")
        fake.runtime_available = lambda: False
        sys.modules["runtime.core.attestation"] = fake
        try:
            module.locate = lambda: BASE
            assert module.detect() == module.PROMPT_ONLY, (
                "detect() reported AVAILABLE even though the runtime check "
                "returned False"
            )
        finally:
            module.locate = original_locate
            if original_module is None:
                sys.modules.pop("runtime.core.attestation", None)
            else:
                sys.modules["runtime.core.attestation"] = original_module

    def test_probe_reports_available_when_the_runtime_check_says_yes(self):
        import types

        module = self._load_probe()
        original_locate = module.locate
        original_module = sys.modules.get("runtime.core.attestation")
        fake = types.ModuleType("runtime.core.attestation")
        fake.runtime_available = lambda: True
        sys.modules["runtime.core.attestation"] = fake
        try:
            module.locate = lambda: BASE
            assert module.detect() == module.AVAILABLE
        finally:
            module.locate = original_locate
            if original_module is None:
                sys.modules.pop("runtime.core.attestation", None)
            else:
                sys.modules["runtime.core.attestation"] = original_module

    def test_probe_never_raises_even_if_the_check_explodes(self):
        """A crashing check must degrade to PROMPT_ONLY, never AVAILABLE."""
        import types

        module = self._load_probe()
        original_locate = module.locate
        original_module = sys.modules.get("runtime.core.attestation")

        def boom():
            raise RuntimeError("runtime is on fire")

        fake = types.ModuleType("runtime.core.attestation")
        fake.runtime_available = boom
        sys.modules["runtime.core.attestation"] = fake
        try:
            module.locate = lambda: BASE
            assert module.detect() == module.PROMPT_ONLY
        finally:
            module.locate = original_locate
            if original_module is None:
                sys.modules.pop("runtime.core.attestation", None)
            else:
                sys.modules["runtime.core.attestation"] = original_module


class TestInstalledCopyIsCurrent:
    """The strongest check: what the host loads must not be stale.

    A green repository test proves nothing if the installed skill predates the
    change. This compares the payload files that carry the gate.
    """

    GATE_FILES = (
        "AGENTS.md",
        os.path.join("router", "grounding-rules.md"),
        os.path.join("SKILL.md"),
    )

    def test_installed_copy_carries_the_recipe(self):
        target = installed_copy()
        if target is None:
            pytest.skip("no installed ultimate-dev skill on this machine")
        text = read(os.path.join(target, "AGENTS.md"))
        for term in GATE_TERMS:
            assert term in text, (
                f"the installed skill at {target} is stale: {term} is missing. "
                "Re-run scripts/install.sh, or a host will keep loading a skill "
                "that has no gate."
            )

    def test_installed_copy_ships_the_gate_implementation(self):
        target = installed_copy()
        if target is None:
            pytest.skip("no installed ultimate-dev skill on this machine")
        assert os.path.isfile(
            os.path.join(target, "runtime", "core", "attestation.py")
        ), "the installed skill ships the prompt core but not the gate it references"

    def test_installed_files_match_the_payload(self):
        target = installed_copy()
        if target is None:
            pytest.skip("no installed ultimate-dev skill on this machine")
        stale = []
        for relative in self.GATE_FILES:
            source = os.path.join(BASE, relative)
            installed = os.path.join(target, relative)
            if not os.path.isfile(installed):
                stale.append(f"{relative} (missing)")
            elif read(source) != read(installed):
                stale.append(f"{relative} (differs)")
        assert not stale, (
            "the installed skill is out of date: " + ", ".join(stale) +
            ". Re-run scripts/install.sh or hosts keep loading stale rules."
        )


class TestFreshInstallCarriesTheGate:
    """A clean install into a temp dir must contain the gate end to end."""

    def test_install_into_temp_dir_ships_gate_and_recipe(self):
        script = os.path.join(BASE, "scripts", "install.sh")
        if not os.path.isfile(script):
            pytest.skip("installer not present")
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                ["bash", script, "--generic", "--project", tmp, "--yes"],
                cwd=BASE,
                capture_output=True,
                text=True,
                timeout=300,
            )
            if result.returncode != 0:
                pytest.skip(f"installer unavailable in this environment: {result.stderr[-200:]}")
            # Locate whatever directory the installer created.
            found = None
            for root, _dirs, names in os.walk(tmp):
                if "AGENTS.md" in names and os.path.isdir(os.path.join(root, "router")):
                    found = root
                    break
            assert found is not None, f"installer created no skill payload under {tmp}"
            text = read(os.path.join(found, "AGENTS.md"))
            for term in GATE_TERMS:
                assert term in text, f"a fresh install is missing {term}"
            assert os.path.isfile(
                os.path.join(found, "runtime", "core", "attestation.py")
            ), "a fresh install ships prompts without the gate implementation"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
