#!/usr/bin/env python3
"""The runtime must contain no model provider and no credential handling.

Model Independence is a stated non-negotiable: never branch on hardcoded model
names, use capabilities. The stronger form of that rule is the one this test
enforces.

``runtime/core/engine.py`` states the boundary in its own docstring:

    "It never imports a model provider or selects a sandbox/browser provider."

A provider client inside ``runtime/`` makes that sentence false, and it is also
a consent problem: such a client reads ``OPENAI_API_KEY`` or
``ANTHROPIC_API_KEY`` out of the environment and spends the user's money on
their behalf, with no configuration and no consent step. That is not a
capability the prompt-first runtime should have. The host already *is* the
intelligence provider; a second, silent one is neither needed nor permitted.

These tests therefore assert an absence rather than a configuration. Deleting
the client was the correct fix, so the assertions describe a property that
cannot regress.
"""
from __future__ import annotations

import os
import re
import sys

import pytest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

#: Credential names the runtime must never read.
CREDENTIAL_ENV = re.compile(
    r"""["']([A-Z0-9_]*(?:API_KEY|ACCESS_TOKEN|SECRET|_TOKEN|CREDENTIAL)[A-Z0-9_]*)["']"""
)

#: Transports the runtime must not use. The runtime executes through host
#: capabilities; it does not open sockets of its own.
TRANSPORTS = (
    "requests.get", "requests.post", "requests.put", "requests.delete",
    "urllib.request", "urlopen(", "httpx.", "aiohttp.", "socket.socket",
    "XMLHttpRequest",
)

#: Vendor model-name prefixes that must never be compiled in.
FORBIDDEN = ("gpt-", "claude-3", "claude-4", "llama3", "gemini-", "mixtral")


def runtime_sources() -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    root = os.path.join(BASE, "runtime")
    for directory, dirs, names in os.walk(root):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for name in names:
            if name.endswith((".py", ".mjs")):
                path = os.path.join(directory, name)
                with open(path, encoding="utf-8") as handle:
                    out.append((os.path.relpath(path, BASE), handle.read()))
    return out


class TestNoProviderClientExists:
    def test_no_model_adapter_module(self):
        for candidate in (
            os.path.join(BASE, "runtime", "core", "model_adapter"),
            os.path.join(BASE, "runtime", "core", "model_adapter.py"),
        ):
            assert not os.path.exists(candidate), (
                f"{candidate} exists. The runtime must not carry a model "
                "provider client: it duplicates a capability the host already "
                "provides and reads the user's API keys without consent."
            )

    def test_no_module_constructs_a_model_adapter(self):
        offenders = []
        for root in ("runtime", "tests", "scripts"):
            for directory, dirs, names in os.walk(os.path.join(BASE, root)):
                dirs[:] = [d for d in dirs if d != "__pycache__"]
                for name in names:
                    if not name.endswith(".py"):
                        continue
                    path = os.path.join(directory, name)
                    with open(path, encoding="utf-8") as handle:
                        text = handle.read()
                    if re.search(r"\bModelAdapter\b|\bcreate_model_adapter\b", text):
                        offenders.append(os.path.relpath(path, BASE))
        assert not offenders, f"model adapter references remain: {offenders}"


class TestNoCredentialHandling:
    def test_runtime_never_reads_a_credential_from_the_environment(self):
        offenders = []
        for relative, text in runtime_sources():
            for number, line in enumerate(text.splitlines(), 1):
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                if "environ" not in stripped and "getenv" not in stripped:
                    continue
                for match in CREDENTIAL_ENV.finditer(stripped):
                    offenders.append(f"{relative}:{number} {match.group(1)}")
        assert not offenders, (
            "the runtime must not read credentials from the environment:\n  "
            + "\n  ".join(offenders)
            + "\nUsing a key the user set for their own tooling, without "
            "consent, is not a capability this runtime should have."
        )

    def test_no_authorization_header_is_built(self):
        offenders = []
        for relative, text in runtime_sources():
            for number, line in enumerate(text.splitlines(), 1):
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                if "Authorization" in stripped or "x-api-key" in stripped:
                    offenders.append(f"{relative}:{number}")
        assert not offenders, (
            f"the runtime must not build an authorization header: {offenders}"
        )


class TestNoDirectNetworkTransport:
    @pytest.mark.parametrize("transport", TRANSPORTS)
    def test_runtime_opens_no_socket_of_its_own(self, transport):
        offenders = []
        for relative, text in runtime_sources():
            # contracts.py and redaction.py *name* transports in order to deny
            # them; naming a transport to forbid it is not using it.
            if relative.endswith(("contracts.py", "redaction.py")):
                continue
            for number, line in enumerate(text.splitlines(), 1):
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                if transport in stripped:
                    offenders.append(f"{relative}:{number}")
        assert not offenders, (
            f"the runtime uses {transport} at {offenders}. Execution goes "
            "through host capabilities; the runtime opens no connection itself."
        )


class TestNoModelNameLiterals:
    def test_runtime_names_no_model(self):
        offenders = []
        for relative, text in runtime_sources():
            for number, line in enumerate(text.splitlines(), 1):
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                for token in FORBIDDEN:
                    if token in stripped:
                        offenders.append(f"{relative}:{number} {token}")
        assert not offenders, f"model names compiled into the runtime: {offenders}"


class TestTheBoundaryIsStatedAndTrue:
    def test_engine_docstring_claims_the_boundary(self):
        """The claim must exist, so removing the client keeps it honest."""
        with open(os.path.join(BASE, "runtime", "core", "engine.py"), encoding="utf-8") as handle:
            text = handle.read()
        assert "never imports a model provider" in text, (
            "engine.py must state the provider boundary; the tests above "
            "enforce it, and a claim nothing checks decays into a lie"
        )

    def test_configuration_remains_the_tier_source(self):
        import yaml

        with open(os.path.join(BASE, "config", "models.yaml"), encoding="utf-8") as handle:
            config = yaml.safe_load(handle)
        assert "tiers" in config, (
            "models.yaml stays the capability and tier source of truth; the "
            "runtime consumes it, it does not embed a provider"
        )


class TestDetectorsAreNotVacuous:
    def test_credential_detector_matches_a_real_offender(self):
        sample = '    key = os.environ.get("ANTHROPIC_API_KEY")'
        assert CREDENTIAL_ENV.search(sample), "the credential detector must match"

    def test_credential_detector_ignores_ordinary_names(self):
        assert not CREDENTIAL_ENV.search('os.environ.get("HOME")')

    def test_model_detector_matches_a_real_offender(self):
        assert any(token in 'model="gpt-4o-mini"' for token in FORBIDDEN)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
