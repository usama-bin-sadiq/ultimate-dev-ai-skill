#!/usr/bin/env python3
"""
Legacy session manager and host-executor seam.

The canonical JEV decision layer is host-native and lives outside this module.
This class preserves the Python Runtime API for compatibility, but it never
selects, installs, or claims to provide a sandbox/browser implementation.
A host adapter may inject an executor for actual actions.
"""
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path



class SandboxMode(Enum):
    DISABLED = "disabled"          # No sandbox at all
    ON_DEMAND = "on_demand"       # Initialize only when task needs it
    ALWAYS = "always"             # Always initialize at session start


@dataclass
class SessionConfig:
    """Legacy session configuration retained for API compatibility."""
    sandbox_mode: SandboxMode = SandboxMode.ON_DEMAND
    sandbox_backend: Optional[str] = None  # legacy compatibility only
    browser_backend: Optional[str] = None  # legacy compatibility only
    auto_install_deps: bool = False  # ignored by the host-native path
    remember_choice: bool = True


class SessionManager:
    """Legacy session API with an optional injected host executor."""
    
    CONFIG_FILE = ".memory/ultimate-dev/session_config.json"
    
    def __init__(self, project_root: str, host_executor=None):
        self.project_root = Path(project_root)
        self.config_path = self.project_root / self.CONFIG_FILE
        self.config = self._load_config()
        self.sandbox_initialized = False
        self.sandbox_backend = None
        self.host_executor = host_executor
        
    def _load_config(self) -> SessionConfig:
        """Load session config from file."""
        if self.config_path.exists():
            try:
                with open(self.config_path) as f:
                    data = json.load(f)
                return SessionConfig(
                    sandbox_mode=SandboxMode(data.get("sandbox_mode", "on_demand")),
                    sandbox_backend=data.get("sandbox_backend"),
                    browser_backend=data.get("browser_backend"),
                    auto_install_deps=data.get("auto_install_deps", False),
                    remember_choice=data.get("remember_choice", True),
                )
            except Exception:
                pass
        return SessionConfig()
    
    def _save_config(self):
        """Save session config to file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "sandbox_mode": self.config.sandbox_mode.value,
            "sandbox_backend": self.config.sandbox_backend,
            "browser_backend": self.config.browser_backend,
            "auto_install_deps": self.config.auto_install_deps,
            "remember_choice": self.config.remember_choice,
        }
        with open(self.config_path, "w") as f:
            json.dump(data, f, indent=2)
    
    def ask_sandbox_preferences(self, interactive: bool = True) -> SessionConfig:
        """Explain the host-native execution seam without selecting a provider.

        The old preference flow is intentionally not run: Ultimate-Dev does
        not install or select a sandbox/browser backend on the user's behalf.
        """
        if interactive:
            print("Ultimate-Dev uses host-native capabilities; no sandbox or browser provider is selected here.")
        return self.config

    def should_initialize_sandbox(self, task_requires_execution: bool = False, task_description: str = "") -> bool:
        """Return whether an injected host executor can handle the request.

        The legacy preference flags remain readable for compatibility, but this
        module never discovers or installs Docker, a browser, or another
        provider. Without an injected executor there is no local action path.
        """
        if self.host_executor is None:
            return False
        if self.config.sandbox_mode == SandboxMode.DISABLED:
            return False
        if self.config.sandbox_mode == SandboxMode.ALWAYS:
            return True
        return bool(task_requires_execution)
    
    def initialize_sandbox(self, force: bool = False) -> bool:
        """Mark the injected host executor as available, if one exists.

        This method intentionally does not probe or install an execution
        backend. The name is retained for source compatibility with the
        legacy Python API.
        """
        if self.host_executor is None:
            return False
        self.sandbox_initialized = True
        self.sandbox_backend = "host_adapter"
        return True
    
    def execute_code(self, code: str, language: str = "python", task_description: str = "", **kwargs) -> Dict[str, Any]:
        """Delegate execution to an explicitly injected host adapter.

        No local fallback is used. A missing adapter is an honest unavailable
        result rather than a fabricated successful execution.
        """
        task_desc = task_description or f"Execute {language} code"
        if not self.should_initialize_sandbox(task_requires_execution=True, task_description=task_desc):
            return {
                "success": False,
                "error": "No host execution adapter is available.",
                "code": "capability_unavailable",
                "stdout": "",
                "stderr": "",
                "exit_code": -1,
            }
        if not self.initialize_sandbox():
            return {
                "success": False,
                "error": "Host execution adapter is unavailable.",
                "code": "capability_unavailable",
                "stdout": "",
                "stderr": "",
                "exit_code": -1,
            }
        return self._execute_in_sandbox(code, language, task_description=task_desc, **kwargs)

    def _execute_in_sandbox(self, code: str, language: str, **kwargs) -> Dict[str, Any]:
        """Delegate to the host adapter without claiming a local sandbox."""
        if self.host_executor is None:
            return {
                "success": False,
                "error": "No host execution adapter is available.",
                "code": "capability_unavailable",
                "stdout": "",
                "stderr": "",
                "exit_code": -1,
            }
        result = self.host_executor(code=code, language=language, **kwargs)
        return dict(result)


def create_session_manager(project_root: str, interactive: bool = True, host_executor=None) -> SessionManager:
    """Factory function for the legacy session API with an optional host adapter."""
    manager = SessionManager(project_root, host_executor=host_executor)
    manager.ask_sandbox_preferences(interactive=interactive)
    return manager


if __name__ == "__main__":
    # Test session manager
    import sys
    project_root = sys.argv[1] if len(sys.argv) > 1 else "."
    manager = create_session_manager(project_root, interactive=True)
    print(f"\nSession config: {manager.config}")
    print(f"Sandbox will initialize: {manager.should_initialize_sandbox(task_requires_execution=True)}")