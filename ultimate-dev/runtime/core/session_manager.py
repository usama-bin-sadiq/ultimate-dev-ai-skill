#!/usr/bin/env python3
"""
Session Manager - Handles session initialization with optional sandbox.
Asks user about sandbox needs at session start.
"""
import os
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

# Jev integration
from runtime.core.jev import JevCore, JevContext, create_jev_core


class SandboxMode(Enum):
    DISABLED = "disabled"          # No sandbox at all
    ON_DEMAND = "on_demand"       # Initialize only when task needs it
    ALWAYS = "always"             # Always initialize at session start


@dataclass
class SessionConfig:
    """Session configuration with sandbox preferences."""
    sandbox_mode: SandboxMode = SandboxMode.ON_DEMAND
    sandbox_backend: Optional[str] = None  # docker, podman, local
    browser_backend: Optional[str] = None  # playwright, puppeteer, selenium
    auto_install_deps: bool = False
    remember_choice: bool = True


class SessionManager:
    """Manages session initialization with optional sandbox."""
    
    CONFIG_FILE = ".memory/ultimate-dev/session_config.json"
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.config_path = self.project_root / self.CONFIG_FILE
        self.config = self._load_config()
        self.sandbox_initialized = False
        self.sandbox_backend = None
        
        # Jev Core integration
        self.jev_core = None
        
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
        """
        Ask user about sandbox preferences at session start.
        Only runs in interactive mode.
        """
        if not interactive:
            return self.config
        
        print("\n" + "=" * 60)
        print("ULTIMATE-DEV SESSION INITIALIZATION")
        print("=" * 60)
        print("\nSandbox layer provides:")
        print("  • Code execution (Python, JS/TS, Go, Rust, Bash)")
        print("  • Browser automation (Playwright)")
        print("  • Secure isolated execution environment")
        print()
        
        if self.config.remember_choice and self.config.sandbox_mode != SandboxMode.DISABLED:
            print(f"Previous setting: {self.config.sandbox_mode.value}")
            use_previous = input("Use previous sandbox setting? [Y/n]: ").lower()
            if use_previous not in ('n', 'no'):
                return self.config
        
        print("Sandbox mode options:")
        print("  1. Disabled      - No sandbox, no execution capabilities")
        print("  2. On Demand     - Initialize only when task needs execution (recommended)")
        print("  3. Always        - Initialize at session start")
        
        choice = input("\nChoose sandbox mode [1/2/3] [2]: ").strip() or "2"
        
        mode_map = {
            "1": SandboxMode.DISABLED,
            "2": SandboxMode.ON_DEMAND,
            "3": SandboxMode.ALWAYS,
        }
        
        self.config.sandbox_mode = mode_map.get(choice, SandboxMode.ON_DEMAND)
        
        if self.config.sandbox_mode != SandboxMode.DISABLED:
            self._ask_backend_preferences()
            self._ask_auto_install()
        
        if self.config.remember_choice:
            self._save_config()
        
        print(f"\n✅ Sandbox mode set to: {self.config.sandbox_mode.value}")
        if self.config.sandbox_backend:
            print(f"   Sandbox backend: {self.config.sandbox_backend}")
        if self.config.browser_backend:
            print(f"   Browser backend: {self.config.browser_backend}")
        
        return self.config
    
    def _ask_backend_preferences(self):
        """Ask user about sandbox and browser backend preferences."""
        print("\nSandbox backend options:")
        print("  1. Docker (recommended)")
        print("  2. Podman (rootless, no daemon)")
        print("  3. Local subprocess (no isolation)")
        print("  4. Auto-detect (recommended)")
        
        choice = input("\nChoose sandbox backend [1/2/3/4] [4]: ").strip() or "4"
        backend_map = {
            "1": "docker",
            "2": "podman", 
            "3": "local",
            "4": "auto",
        }
        self.config.sandbox_backend = backend_map.get(choice, "auto")
        
        print("\nBrowser backend options:")
        print("  1. Playwright (recommended - multi-browser)")
        print("  2. Puppeteer (Chrome only)")
        print("  3. Selenium (legacy)")
        print("  4. Auto-detect (recommended)")
        
        choice = input("\nChoose browser backend [1/2/3/4] [4]: ").strip() or "4"
        browser_map = {
            "1": "playwright",
            "2": "puppeteer",
            "3": "selenium",
            "4": "auto",
        }
        self.config.browser_backend = browser_map.get(choice, "auto")
    
    def _ask_auto_install(self):
        """Ask about auto-installing missing dependencies."""
        choice = input("\nAuto-install missing dependencies? [y/N]: ").strip().lower()
        self.config.auto_install_deps = choice in ('y', 'yes')
    
    def should_initialize_sandbox(self, task_requires_execution: bool = False, task_description: str = "") -> bool:
        """Determine if sandbox should be initialized using Jev for decision making."""
        if self.config.sandbox_mode == SandboxMode.DISABLED:
            return False
        if self.config.sandbox_mode == SandboxMode.ALWAYS:
            return True
        if self.config.sandbox_mode == SandboxMode.ON_DEMAND:
            # Use Jev for intelligent decision making
            if self.jev_core and task_description:
                jev_decision = self.jev_core.classify(JevContext(
                    user_input=task_description,
                    langchain_state={},
                    available_tools=[],
                    session_config={"sandbox_mode": self.config.sandbox_mode.value},
                    project_root=str(self.project_root)
                ))
                # Use Jev's decision for execution
                return jev_decision.get("should_execute", task_requires_execution)
            return task_requires_execution
        return False
    
    def initialize_sandbox(self, force: bool = False) -> bool:
        """
        Initialize sandbox backend lazily.
        Returns True if sandbox is available, False if disabled/unavailable.
        """
        if self.sandbox_initialized and not force:
            return self.sandbox_backend is not None
        
        if self.config.sandbox_mode == SandboxMode.DISABLED:
            print("ℹ️  Sandbox disabled by user preference")
            return False
        
        # Import here to avoid circular imports
        from runtime.core.sandbox.dependency_manager import SandboxDependencyManager
        
        mgr = SandboxDependencyManager(auto_install=False, interactive=False)
        backend = self.config.sandbox_backend
        
        if backend == "auto" or backend is None:
            backend = mgr.get_available_backend("sandbox")
        
        if backend:
            status, version = mgr.check_dependency(backend)
            if status == "available":
                self.sandbox_backend = backend
                self.sandbox_initialized = True
                print(f"✅ Sandbox initialized: {backend} v{version}")
                return True
            else:
                print(f"⚠️  Preferred backend '{backend}' not available")
        
        # Try fallback
        fallback = "podman" if backend == "docker" else "local"
        status, _ = mgr.check_dependency(fallback)
        if status == "available":
            self.sandbox_backend = fallback
            self.sandbox_initialized = True
            print(f"✅ Sandbox initialized (fallback): {fallback}")
            return True
        
        print("ℹ️  No sandbox backend available - execution disabled")
        return False
    
    def execute_code(self, code: str, language: str = "python", task_description: str = "", **kwargs) -> Dict[str, Any]:
        """
        Execute code in sandbox (lazy initialization with Jev decision making).
        Returns result dict with stdout, stderr, exit_code, etc.
        """
        # Use Jev for intelligent decision making
        task_desc = task_description or f"Execute {language} code"
        if not self.should_initialize_sandbox(task_requires_execution=True, task_description=task_desc):
            return {
                "success": False,
                "error": "Sandbox not initialized. Enable sandbox mode or ensure task requires execution.",
                "stdout": "",
                "stderr": "",
                "exit_code": -1,
            }
        
        if not self.initialize_sandbox():
            return {
                "success": False,
                "error": "No sandbox backend available",
                "stdout": "",
                "stderr": "",
                "exit_code": -1,
            }
        
        # Delegate to actual sandbox implementation
        return self._execute_in_sandbox(code, language, **kwargs)
    
    def _execute_in_sandbox(self, code: str, language: str, **kwargs) -> Dict[str, Any]:
        """Execute code in the initialized sandbox backend."""
        # This would delegate to the actual sandbox implementation
        # For now, return a placeholder
        return {
            "success": True,
            "stdout": f"[Executed {language} code in {self.sandbox_backend}]",
            "stderr": "",
            "exit_code": 0,
            "backend": self.sandbox_backend,
        }


def create_session_manager(project_root: str, interactive: bool = True) -> SessionManager:
    """Factory function to create and initialize session manager."""
    manager = SessionManager(project_root)
    manager.ask_sandbox_preferences(interactive=interactive)
    return manager


if __name__ == "__main__":
    # Test session manager
    import sys
    project_root = sys.argv[1] if len(sys.argv) > 1 else "."
    manager = create_session_manager(project_root, interactive=True)
    print(f"\nSession config: {manager.config}")
    print(f"Sandbox will initialize: {manager.should_initialize_sandbox(task_requires_execution=True)}")