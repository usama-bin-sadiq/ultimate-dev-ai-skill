"""
Sandbox Runner - Real execution backend for code execution.
Supports Docker, Podman, and local subprocess fallback.
"""
from __future__ import annotations
import os
import subprocess
import tempfile
import json
import shutil
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import uuid


class SandboxBackend(Enum):
    DOCKER = "docker"
    PODMAN = "podman"
    LOCAL = "local"


@dataclass
class SandboxConfig:
    backend: SandboxBackend = SandboxBackend.DOCKER
    cpu_limit: str = "1.0"
    memory_limit: str = "512m"
    timeout_seconds: int = 120
    network_mode: str = "none"  # none, bridge, host
    working_dir: str = "/workspace"
    image: str = "python:3.11-slim"
    volumes: List[str] = field(default_factory=list)


@dataclass
class ExecutionResult:
    success: bool
    stdout: str = ""
    stderr: str = ""
    exit_code: int = -1
    execution_time_ms: float = 0.0
    backend_used: str = ""
    error: Optional[str] = None


class SandboxRunner:
    """
    Sandbox Runner - Executes code in isolated environments.
    Supports Docker, Podman, and local subprocess fallback.
    """
    
    def __init__(self, config: Optional[SandboxConfig] = None):
        self.config = config or SandboxConfig()
        self.backend = self._detect_backend()
        
    def _detect_backend(self) -> SandboxBackend:
        """Auto-detect available sandbox backend."""
        # Check Docker
        if self._check_command(["docker", "version"]):
            return SandboxBackend.DOCKER
        # Check Podman
        if self._check_command(["podman", "version"]):
            return SandboxBackend.PODMAN
        # Fallback to local
        return SandboxBackend.LOCAL
    
    def _check_command(self, cmd: List[str]) -> bool:
        try:
            result = subprocess.run(cmd, capture_output=True, timeout=5)
            return result.returncode == 0
        except:
            return False
    
    def execute(self, code: str, language: str = "python", **kwargs) -> ExecutionResult:
        """Execute code in sandbox."""
        import time
        start = time.perf_counter()
        
        if self.backend == SandboxBackend.DOCKER:
            return self._execute_docker(code, language)
        elif self.backend == SandboxBackend.PODMAN:
            return self._execute_podman(code, language)
        else:
            return self._execute_local(code, language)
    
    def _execute_docker(self, code: str, language: str) -> ExecutionResult:
        """Execute code in Docker container."""
        import time
        start = time.perf_counter()
        
        # Write code to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix=f'.{self._get_extension("python")}', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        try:
            # Copy file to container and execute
            container_name = f"ultimate-dev-{uuid.uuid4().hex[:8]}"
            
            # Build docker command
            cmd = [
                "docker", "run", "--rm",
                "--name", container_name,
                "--cpus", "1.0",
                "--memory", "512m",
                "--network", "none",
                "-v", f"{temp_file}:/workspace/code.py:ro",
                "-w", "/workspace",
                "python:3.11-slim",
                "python", "code.py"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            execution_time = (time.perf_counter() - start) * 1000
            
            return ExecutionResult(
                success=result.returncode == 0,
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.returncode,
                execution_time_ms=execution_time,
                backend_used="docker"
            )
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                success=False,
                error="Execution timeout",
                execution_time_ms=(time.perf_counter() - start) * 1000,
                backend_used="docker"
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                error=str(e),
                execution_time_ms=(time.perf_counter() - start) * 1000,
                backend_used="docker"
            )
        finally:
            # Cleanup
            try:
                os.unlink(temp_file)
            except:
                pass
    
    def _execute_podman(self, code: str, language: str) -> ExecutionResult:
        """Execute code in Podman container."""
        # Similar to Docker but with podman command
        return self._execute_docker(code, language)  # Same logic for now
    
    def _execute_local(self, code: str, language: str) -> ExecutionResult:
        """Execute code locally (fallback, no isolation)."""
        import time
        start = time.perf_counter()
        
        ext = self._get_extension("python")
        with tempfile.NamedTemporaryFile(mode='w', suffix=ext, delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        try:
            cmd = ["python3", temp_file] if language == "python" else ["bash", temp_file]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            execution_time = (time.perf_counter() - start) * 1000
            
            return ExecutionResult(
                success=result.returncode == 0,
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.returncode,
                execution_time_ms=execution_time,
                backend_used="local"
            )
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                success=False,
                error="Execution timeout",
                backend_used="local"
            )
        except Exception as e:
            return ExecutionResult(success=False, error=str(e), backend_used="local")
        finally:
            try:
                os.unlink(temp_file)
            except:
                pass
    
    def _get_extension(self, language: str) -> str:
        extensions = {"python": ".py", "javascript": ".js", "typescript": ".ts", "bash": ".sh"}
        return extensions.get(language, ".txt")
    
    def is_available(self) -> bool:
        return self.backend != SandboxBackend.LOCAL or self._check_command(["python3"])
    
    def get_backend_info(self) -> Dict[str, Any]:
        return {
            "backend": self.backend.value,
            "available": self.is_available(),
        }


# Factory
def create_sandbox_runner(config: Optional[Dict] = None):
    return SandboxRunner(config)