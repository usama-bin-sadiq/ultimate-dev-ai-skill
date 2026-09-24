#!/usr/bin/env python3
"""
Sandbox Dependency Manager - Handles OS-level dependencies gracefully.
Auto-detects, installs (with consent), and provides graceful degradation.
"""
import os
import subprocess
import shutil
import platform
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class DependencyStatus(Enum):
    AVAILABLE = "available"
    MISSING = "missing"
    OUTDATED = "outdated"
    ERROR = "error"


@dataclass
class Dependency:
    name: str
    check_command: List[str]
    install_commands: Dict[str, List[str]]  # per platform
    min_version: Optional[str] = None
    required: bool = False
    fallback: Optional[str] = None


class SandboxDependencyManager:
    """Manages OS-level dependencies for sandbox execution with graceful degradation."""
    
    DEPENDENCIES = {
        "docker": Dependency(
            name="docker",
            check_command=["docker", "version", "--format", "{{.Server.Version}}"],
            install_commands={
                "darwin": ["brew install --cask docker"],
                "linux": ["curl -fsSL https://get.docker.com | sh"],
                "windows": ["winget install Docker.DockerDesktop"],
            },
            min_version="20.10.0",
            required=True,
            fallback="podman",
        ),
        "podman": Dependency(
            name="podman",
            check_command=["podman", "version"],
            install_commands={
                "darwin": ["brew install podman"],
                "linux": ["sudo apt-get install -y podman", "sudo dnf install -y podman", "sudo pacman -S podman"],
                "windows": ["winget install RedHat.Podman"],
            },
            min_version="4.0.0",
            required=False,
            fallback="local",
        ),
        "playwright": Dependency(
            name="playwright",
            check_command=["playwright", "--version"],
            install_commands={
                "darwin": ["pip install playwright && playwright install"],
                "linux": ["pip install playwright && playwright install"],
                "windows": ["pip install playwright && playwright install"],
            },
            min_version="1.40.0",
            required=True,
            fallback="puppeteer",
        ),
        "puppeteer": Dependency(
            name="puppeteer",
            check_command=["npx", "puppeteer", "--version"],
            install_commands={
                "darwin": ["npm install -g puppeteer"],
                "linux": ["npm install -g puppeteer"],
                "windows": ["npm install -g puppeteer"],
            },
            min_version="21.0.0",
            required=False,
            fallback="selenium",
        ),
    }

    def __init__(self, auto_install: bool = False, interactive: bool = True):
        self.auto_install = auto_install
        self.interactive = interactive
        self.platform = self._detect_platform()
        self.status_cache: Dict[str, DependencyStatus] = {}
        self.version_cache: Dict[str, str] = {}

    def _detect_platform(self) -> str:
        system = platform.system().lower()
        if system == "darwin":
            return "darwin"
        elif system == "linux":
            return "linux"
        elif system == "windows":
            return "windows"
        return "unknown"

    def check_dependency(self, name: str) -> Tuple[DependencyStatus, Optional[str]]:
        """Check if a dependency is available and get its version."""
        if name in self.status_cache:
            return self.status_cache[name], self.version_cache.get(name)

        dep = self.DEPENDENCIES.get(name)
        if not dep:
            return DependencyStatus.ERROR, None

        try:
            result = subprocess.run(
                dep.check_command,
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                version = result.stdout.strip()
                self.version_cache[name] = version
                
                # Check minimum version
                if dep.min_version and not self._version_satisfies(version, dep.min_version):
                    self.status_cache[name] = DependencyStatus.OUTDATED
                    return DependencyStatus.OUTDATED, version
                
                self.status_cache[name] = DependencyStatus.AVAILABLE
                return DependencyStatus.AVAILABLE, version
            else:
                self.status_cache[name] = DependencyStatus.MISSING
                return DependencyStatus.MISSING, None
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            self.status_cache[name] = DependencyStatus.MISSING
            return DependencyStatus.MISSING, None

    def _version_satisfies(self, current: str, minimum: str) -> bool:
        """Check if current version satisfies minimum requirement."""
        try:
            current_parts = [int(x) for x in current.split(".")[:3]]
            min_parts = [int(x) for x in minimum.split(".")[:3]]
            return current_parts >= min_parts
        except (ValueError, IndexError):
            return True  # Assume compatible if can't parse

    def install_dependency(self, name: str) -> bool:
        """Install a dependency using platform-appropriate method."""
        dep = self.DEPENDENCIES.get(name)
        if not dep:
            print(f"Unknown dependency: {name}")
            return False

        commands = dep.install_commands.get(self.platform)
        if not commands:
            print(f"No install command for {name} on {self.platform}")
            return False

        if self.interactive and not self.auto_install:
            response = input(f"\n{name} is required but not found. Install automatically? [y/N]: ")
            if response.lower() not in ('y', 'yes'):
                print(f"Skipping {name} installation.")
                return False

        print(f"Installing {name}...")
        for cmd in commands if isinstance(commands, list) else [commands]:
            try:
                print(f"  Running: {cmd}")
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
                if result.returncode != 0:
                    print(f"  Failed: {result.stderr}")
                    return False
            except subprocess.TimeoutExpired:
                print(f"  Timeout installing {name}")
                return False
            except Exception as e:
                print(f"  Error: {e}")
                return False

        # Verify installation
        status, version = self.check_dependency(name)
        if status == DependencyStatus.AVAILABLE:
            print(f"✅ {name} {version} installed successfully")
            return True
        else:
            print(f"❌ {name} installation verification failed")
            return False

    def check_all(self) -> Dict[str, Tuple[DependencyStatus, Optional[str]]]:
        """Check all dependencies and return status."""
        results = {}
        for name in self.DEPENDENCIES:
            results[name] = self.check_dependency(name)
        return results

    def get_available_backend(self, backend_type: str) -> Optional[str]:
        """Get the best available backend for a given type."""
        if backend_type == "sandbox":
            for backend in ["docker", "podman"]:
                status, _ = self.check_dependency(backend)
                if status == DependencyStatus.AVAILABLE:
                    return backend
            return "local"  # Always available as last resort
        
        elif backend_type == "browser":
            for backend in ["playwright", "puppeteer", "selenium"]:
                status, _ = self.check_dependency(backend)
                if status == DependencyStatus.AVAILABLE:
                    return backend
            return None
        
        return None

    def print_status_report(self) -> None:
        """Print a formatted status report."""
        print("\n" + "=" * 60)
        print("DEPENDENCY STATUS REPORT")
        print("=" * 60)
        
        for name, dep in self.DEPENDENCIES.items():
            status, version = self.check_dependency(name)
            status_icon = {
                DependencyStatus.AVAILABLE: "✅",
                DependencyStatus.OUTDATED: "⚠️",
                DependencyStatus.MISSING: "❌",
                DependencyStatus.ERROR: "💥",
            }.get(status, "❓")
            
            version_str = f" v{version}" if version else ""
            required_str = " (REQUIRED)" if dep.required else ""
            fallback_str = f" → fallback: {dep.fallback}" if dep.fallback and status != DependencyStatus.AVAILABLE else ""
            
            print(f"  {status_icon} {name}{version_str}{required_str}{fallback_str}")
        
        print("=" * 60)


# Convenience function for quick checks
def check_sandbox_dependencies(auto_install: bool = False) -> Dict[str, bool]:
    """Quick check for sandbox dependencies."""
    manager = SandboxDependencyManager(auto_install=auto_install)
    results = {}
    
    # Check sandbox backends
    for backend in ["docker", "podman"]:
        status, _ = manager.check_dependency(backend)
        results[f"sandbox_{backend}"] = status == DependencyStatus.AVAILABLE
    
    # Check browser backends
    for backend in ["playwright", "puppeteer"]:
        status, _ = manager.check_dependency(backend)
        results[f"browser_{backend}"] = status == DependencyStatus.AVAILABLE
    
    # Always available fallback
    results["sandbox_local"] = True
    
    return results


if __name__ == "__main__":
    import sys
    
    auto_install = "--auto-install" in sys.argv
    manager = SandboxDependencyManager(auto_install=auto_install, interactive=True)
    
    print("Checking sandbox dependencies...")
    manager.print_status_report()
    
    # Show recommended backends
    print("\nRecommended backends:")
    sandbox = manager.get_available_backend("sandbox")
    browser = manager.get_available_backend("browser")
    print(f"  Sandbox: {sandbox}")
    print(f"  Browser: {browser}")
    
    if manager.interactive and not auto_install:
        # Offer to install missing required deps
        for name, dep in manager.DEPENDENCIES.items():
            if dep.required:
                status, _ = manager.check_dependency(name)
                if status != DependencyStatus.AVAILABLE:
                    if input(f"\nInstall missing required dependency '{name}'? [y/N]: ").lower() in ('y', 'yes'):
                        manager.install_dependency(name)