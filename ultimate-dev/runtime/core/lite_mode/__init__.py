#!/usr/bin/env python3
"""
Lite Mode — Fast path for atomic tasks.
Skips heavy bootstrap when task is clearly atomic/single-domain.
"""
import os
import json
import hashlib
import tempfile
import time
from pathlib import Path
from typing import Dict, Any, Optional
from functools import lru_cache


MAX_CACHE_BYTES = 1_000_000


def _contained_cache_path(root: Path, key: str) -> Path:
    if not isinstance(key, str) or not key or len(key) > 512:
        raise ValueError("cache key must be a non-empty bounded string")
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
    candidate = root / f"{digest}.json"
    resolved_root = root.resolve()
    resolved = candidate.resolve()
    if resolved != resolved_root and resolved_root not in resolved.parents:
        raise ValueError("cache path escapes project memory")
    if candidate.is_symlink():
        raise ValueError("cache path must not be a symlink")
    return candidate


def _atomic_json_write(path: Path, value: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        raise ValueError("cache path must not be a symlink")
    fd, temporary = tempfile.mkstemp(prefix=".lite-cache-", dir=path.parent)
    try:
        encoded = json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False)
        if len(encoded.encode("utf-8")) > MAX_CACHE_BYTES:
            raise ValueError("cache payload exceeds the bounded size limit")
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)

class LiteMode:
    """Fast-path execution for atomic tasks."""
    
    # Complex and destructive signals are evaluated first and always win over
    # lexical atomic hints. Lite mode must never bypass discovery or review.
    DESTRUCTIVE_INDICATORS = [
        "delete", "remove", "rm -rf", "drop database", "production deploy",
        "rotate credentials", "force push", "secret", "credential", "token",
    ]

    # Task patterns that indicate atomic work
    ATOMIC_INDICATORS = [
        "explain", "describe", "what is", "how to", "show me", "write a",
        "create a function", "write a script", "fix typo", "update doc",
        "refactor", "rename", "add comment", "format", "lint", "test",
        "debug", "why does", "what does", "help me understand"
    ]
    
    # Task patterns that indicate multi-domain/complex work
    COMPLEX_INDICATORS = [
        "build", "deploy", "architect", "design system", "full stack",
        "microservice", "pipeline", "infrastructure", "security audit",
        "migrate", "refactor system", "implement feature", "new project"
    ]
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root).resolve()
        cache_dir = self.project_root / ".memory" / "ultimate-dev" / "lite_cache"
        resolved = cache_dir.resolve()
        if resolved != self.project_root and self.project_root not in resolved.parents:
            raise ValueError("lite cache escapes project root")
        if cache_dir.is_symlink():
            raise ValueError("lite cache directory must not be a symlink")
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def should_use_lite(self, task_description: str) -> bool:
        """Determine if task should use lite mode (atomic path)."""
        if not isinstance(task_description, str) or not task_description.strip():
            return False
        task_lower = task_description.lower()

        # Safety signals take precedence over all optimization hints.
        if any(indicator in task_lower for indicator in self.DESTRUCTIVE_INDICATORS):
            return False
        if any(indicator in task_lower for indicator in self.COMPLEX_INDICATORS):
            return False

        # Only an explicit, unambiguous atomic request may use the fast path.
        return any(indicator in task_lower for indicator in self.ATOMIC_INDICATORS)
    
    def get_cached_init(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached initialization data."""
        cache_file = _contained_cache_path(self.cache_dir, key)
        if cache_file.exists():
            try:
                with open(cache_file, encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict) and self._is_cache_valid(data):
                    return data
            except (OSError, json.JSONDecodeError, TypeError, ValueError):
                pass
        return None
    
    def set_cached_init(self, key: str, data: Dict[str, Any]) -> None:
        """Cache initialization data safely and atomically."""
        cache_file = _contained_cache_path(self.cache_dir, key)
        value = dict(data)
        value["_cache_hash"] = self._compute_skill_hash()
        _atomic_json_write(cache_file, value)

    def cleanup(self, max_age_seconds: float = 86400.0, now: Optional[float] = None) -> int:
        """Remove old cache entries while refusing symlink targets."""
        if max_age_seconds < 0:
            raise ValueError("max_age_seconds must be non-negative")
        current = time.time() if now is None else now
        removed = 0
        for path in self.cache_dir.glob("*.json"):
            if path.is_symlink():
                continue
            try:
                if current - path.stat().st_mtime >= max_age_seconds:
                    path.unlink()
                    removed += 1
            except FileNotFoundError:
                continue
        return removed
    
    def _compute_skill_hash(self) -> str:
        """Compute hash of skill files for cache invalidation."""
        hasher = hashlib.sha256()
        for skill_file in ["SKILL.md", "AGENTS.md", "VERSION"]:
            path = self.project_root / skill_file
            if path.exists():
                hasher.update(path.read_bytes())
        return hasher.hexdigest()
    
    def _is_cache_valid(self, cached_data: Dict) -> bool:
        """Check if cached data is still valid."""
        return cached_data.get("_cache_hash") == self._compute_skill_hash()
    
    def get_lite_config(self) -> Dict[str, Any]:
        """Get lite mode configuration."""
        return {
            "mode": "lite",
            "skip_preflight": False,
            "default_pattern": "A",
            "max_agents": 1,
            "context_levels": ["L0", "L1", "L2"],
            "verification": "standard",
            "state_persistence": "full"
        }


class BootstrapCache:
    """Cache for bootstrap initialization across session turns."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root).resolve()
        cache_file = self.project_root / ".memory" / "ultimate-dev" / "bootstrap_cache.json"
        resolved = cache_file.resolve()
        if resolved != self.project_root and self.project_root not in resolved.parents:
            raise ValueError("bootstrap cache escapes project root")
        if cache_file.is_symlink():
            raise ValueError("bootstrap cache must not be a symlink")
        self.cache_file = cache_file
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
    
    def get(self) -> Optional[Dict[str, Any]]:
        """Get cached bootstrap data."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict) and self._is_valid(data):
                    return data
            except (OSError, json.JSONDecodeError, TypeError, ValueError):
                pass
        return None
    
    def set(self, data: Dict[str, Any]) -> None:
        """Set bootstrap cache atomically."""
        value = dict(data)
        value["_skill_hash"] = self._compute_skill_hash()
        version_path = self.project_root / "VERSION"
        value["_timestamp"] = os.path.getmtime(version_path) if version_path.exists() else 0
        _atomic_json_write(self.cache_file, value)
    
    def _compute_skill_hash(self) -> str:
        hasher = hashlib.sha256()
        for skill_file in ["SKILL.md", "AGENTS.md", "VERSION"]:
            path = self.project_root / skill_file
            if path.exists():
                hasher.update(path.read_bytes())
        return hasher.hexdigest()
    
    def _is_valid(self, data: Dict) -> bool:
        version_path = self.project_root / "VERSION"
        timestamp = os.path.getmtime(version_path) if version_path.exists() else 0
        return (data.get("_skill_hash") == self._compute_skill_hash() and
                data.get("_timestamp") == timestamp)
    
    def invalidate(self) -> None:
        """Invalidate cache."""
        if self.cache_file.exists():
            self.cache_file.unlink()


def create_lite_mode(project_root: str) -> LiteMode:
    """Factory function."""
    return LiteMode(project_root)


def create_bootstrap_cache(project_root: str) -> BootstrapCache:
    """Factory function."""
    return BootstrapCache(project_root)