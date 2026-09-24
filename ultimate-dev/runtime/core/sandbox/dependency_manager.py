#!/usr/bin/env python3
"""Retired sandbox dependency-manager compatibility surface.

The historical manager installed operating-system packages and browser drivers
with shell command strings and remote installer pipelines.  That
surface is not a safe execution boundary.  The module remains importable for
old callers, but it refuses to perform dependency installation.  An explicit
``unsafe_development=True`` is required even for read-only probes; installation
itself always raises :class:`UnsafeDevelopmentError` before any subprocess or
input handling.
"""
from __future__ import annotations

import platform
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple


class LegacyUnavailableError(RuntimeError):
    """Stable typed error for the retired dependency manager."""

    code = "legacy_unavailable"
    error_code = code

    def __init__(
        self,
        component: str = "runtime.core.sandbox.dependency_manager",
        operation: str = "legacy entry point",
    ) -> None:
        self.component = component
        self.operation = operation
        super().__init__(
            f"{self.code}: {component}.{operation} is unavailable; use a "
            "reviewed host capability or an isolated runtime adapter"
        )

    def to_dict(self) -> Dict[str, str]:
        return {
            "code": self.code,
            "component": self.component,
            "operation": self.operation,
            "message": str(self),
        }


class UnsafeDevelopmentError(RuntimeError):
    """Stable typed error for installation paths that cannot be made safe here."""

    code = "unsafe-development"
    error_code = code

    def __init__(
        self,
        component: str = "runtime.core.sandbox.dependency_manager",
        operation: str = "dependency installation",
    ) -> None:
        self.component = component
        self.operation = operation
        super().__init__(
            f"{self.code}: {component}.{operation} is disabled; install "
            "dependencies through a reviewed, isolated host capability"
        )

    def to_dict(self) -> Dict[str, str]:
        return {
            "code": self.code,
            "component": self.component,
            "operation": self.operation,
            "message": str(self),
        }


LegacyUnavailable = LegacyUnavailableError
UnsafeDevelopment = UnsafeDevelopmentError


class DependencyStatus(Enum):
    AVAILABLE = "available"
    MISSING = "missing"
    OUTDATED = "outdated"
    ERROR = "error"


@dataclass
class Dependency:
    name: str
    check_command: List[str]
    # Kept as an empty, inert mapping for source compatibility.  No legacy
    # command is executable by this module.
    install_commands: Dict[str, List[str]] = field(default_factory=dict)
    min_version: Optional[str] = None
    required: bool = False
    fallback: Optional[str] = None


class SandboxDependencyManager:
    """Legacy manager that fails closed unless explicitly used for probing.

    ``unsafe_development`` only permits the read-only ``check_*`` methods.  It
    does not enable installation, shell execution, or a host execution
    fallback.
    """

    READ_ONLY_COMMANDS = frozenset({"docker", "podman", "playwright", "npx"})

    DEPENDENCIES = {
        "docker": Dependency(
            name="docker",
            check_command=["docker", "version", "--format", "{{.Server.Version}}"],
            min_version="20.10.0",
            required=True,
            fallback="podman",
        ),
        "podman": Dependency(
            name="podman",
            check_command=["podman", "version"],
            min_version="4.0.0",
            required=False,
            fallback=None,
        ),
        "playwright": Dependency(
            name="playwright",
            check_command=["playwright", "--version"],
            min_version="1.40.0",
            required=True,
            fallback="puppeteer",
        ),
        "puppeteer": Dependency(
            name="puppeteer",
            check_command=["npx", "--no-install", "puppeteer", "--version"],
            min_version="21.0.0",
            required=False,
            fallback=None,
        ),
    }

    def __init__(
        self,
        auto_install: bool = False,
        interactive: bool = True,
        *,
        unsafe_development: bool = False,
    ) -> None:
        if not unsafe_development:
            raise LegacyUnavailableError(
                "runtime.core.sandbox.dependency_manager",
                "SandboxDependencyManager",
            )
        self.auto_install = auto_install
        self.interactive = interactive
        self.platform = self._detect_platform()
        self.status_cache: Dict[str, DependencyStatus] = {}
        self.version_cache: Dict[str, str] = {}

    @staticmethod
    def _detect_platform() -> str:
        system = platform.system().lower()
        if system in {"darwin", "linux", "windows"}:
            return system
        return "unknown"

    def check_dependency(self, name: str) -> Tuple[DependencyStatus, Optional[str]]:
        """Run a bounded, read-only probe in explicit development mode."""
        if name in self.status_cache:
            return self.status_cache[name], self.version_cache.get(name)

        dep = self.DEPENDENCIES.get(name)
        if dep is None:
            return DependencyStatus.ERROR, None
        if (
            not dep.check_command
            or dep.check_command[0] not in self.READ_ONLY_COMMANDS
            or any(not isinstance(arg, str) or "\x00" in arg for arg in dep.check_command)
        ):
            self.status_cache[name] = DependencyStatus.ERROR
            return DependencyStatus.ERROR, None

        try:
            result = subprocess.run(
                list(dep.check_command),
                shell=False,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired, subprocess.SubprocessError):
            self.status_cache[name] = DependencyStatus.MISSING
            return DependencyStatus.MISSING, None

        if result.returncode != 0:
            self.status_cache[name] = DependencyStatus.MISSING
            return DependencyStatus.MISSING, None

        version = result.stdout.strip()
        self.version_cache[name] = version
        if dep.min_version and not self._version_satisfies(version, dep.min_version):
            self.status_cache[name] = DependencyStatus.OUTDATED
            return DependencyStatus.OUTDATED, version

        self.status_cache[name] = DependencyStatus.AVAILABLE
        return DependencyStatus.AVAILABLE, version

    @staticmethod
    def _version_satisfies(current: str, minimum: str) -> bool:
        """Compare numeric version prefixes without failing open on bad input."""
        try:
            current_parts = [int(part) for part in current.split(".")[:3]]
            minimum_parts = [int(part) for part in minimum.split(".")[:3]]
        except (TypeError, ValueError, IndexError):
            return False
        if not current_parts:
            return False
        width = max(len(current_parts), len(minimum_parts))
        current_parts.extend([0] * (width - len(current_parts)))
        minimum_parts.extend([0] * (width - len(minimum_parts)))
        return tuple(current_parts) >= tuple(minimum_parts)

    def install_dependency(self, name: str) -> bool:
        """Always fail closed before inspecting input or spawning a process."""
        raise UnsafeDevelopmentError(
            "runtime.core.sandbox.dependency_manager",
            "install_dependency",
        )

    def check_all(self) -> Dict[str, Tuple[DependencyStatus, Optional[str]]]:
        return {name: self.check_dependency(name) for name in self.DEPENDENCIES}

    def get_available_backend(self, backend_type: str) -> Optional[str]:
        """Return only a detected isolated backend; never claim host isolation."""
        if backend_type == "sandbox":
            for backend in ("docker", "podman"):
                status, _ = self.check_dependency(backend)
                if status == DependencyStatus.AVAILABLE:
                    return backend
            return None
        if backend_type == "browser":
            for backend in ("playwright", "puppeteer"):
                status, _ = self.check_dependency(backend)
                if status == DependencyStatus.AVAILABLE:
                    return backend
            return None
        return None

    def print_status_report(self) -> None:
        print("\n" + "=" * 60)
        print("DEPENDENCY STATUS REPORT (read-only legacy probe)")
        print("=" * 60)
        for name, dep in self.DEPENDENCIES.items():
            status, version = self.check_dependency(name)
            icon = {
                DependencyStatus.AVAILABLE: "✅",
                DependencyStatus.OUTDATED: "⚠️",
                DependencyStatus.MISSING: "❌",
                DependencyStatus.ERROR: "💥",
            }.get(status, "❓")
            version_text = f" v{version}" if version else ""
            required_text = " (REQUIRED)" if dep.required else ""
            print(f"  {icon} {name}{version_text}{required_text}")
        print("=" * 60)


def check_sandbox_dependencies(
    auto_install: bool = False,
    *,
    unsafe_development: bool = False,
) -> Dict[str, bool]:
    """Run read-only probes only when explicitly requested by a developer."""
    manager = SandboxDependencyManager(
        auto_install=auto_install,
        unsafe_development=unsafe_development,
    )
    results = {
        f"sandbox_{backend}": manager.check_dependency(backend)[0]
        == DependencyStatus.AVAILABLE
        for backend in ("docker", "podman")
    }
    results.update(
        {
            f"browser_{backend}": manager.check_dependency(backend)[0]
            == DependencyStatus.AVAILABLE
            for backend in ("playwright", "puppeteer")
        }
    )
    # An unscoped host process is not an isolated execution backend, so the
    # compatibility key is explicitly false rather than claiming isolation.
    results["sandbox_local"] = False
    return results


__all__ = [
    "LegacyUnavailableError",
    "LegacyUnavailable",
    "UnsafeDevelopmentError",
    "UnsafeDevelopment",
    "DependencyStatus",
    "Dependency",
    "SandboxDependencyManager",
    "check_sandbox_dependencies",
]


if __name__ == "__main__":
    import sys

    try:
        development_mode = "--unsafe-development" in sys.argv
        manager = SandboxDependencyManager(
            auto_install=False,
            interactive=True,
            unsafe_development=development_mode,
        )
    except (LegacyUnavailableError, UnsafeDevelopmentError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2)

    print("Checking sandbox dependencies (read-only)...")
    manager.print_status_report()
    print("\nRecommended sandbox backend:", manager.get_available_backend("sandbox"))
    print("Recommended browser backend:", manager.get_available_backend("browser"))
