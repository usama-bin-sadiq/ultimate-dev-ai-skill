#!/usr/bin/env python3
"""
Lite Mode — Fast path for atomic tasks.
Skips heavy bootstrap when task is clearly atomic/single-domain.
"""
import os
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional
from functools import lru_cache

class LiteMode:
    """Fast-path execution for atomic tasks."""
    
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
        self.project_root = Path(project_root)
        self.cache_dir = self.project_root / ".memory" / "ultimate-dev" / "lite_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def should_use_lite(self, task_description: str) -> bool:
        """Determine if task should use lite mode (atomic path)."""
        task_lower = task_description.lower()
        
        # Check for explicit atomic indicators
        for indicator in self.ATOMIC_INDICATORS:
            if indicator in task_lower:
                return True
        
        # Check for complex indicators (override atomic)
        for indicator in self.COMPLEX_INDICATORS:
            if indicator in task_lower:
                return False
        
        # Default to lite for short tasks
        return len(task_description.split()) < 50
    
    def get_cached_init(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached initialization data."""
        cache_file = self.cache_dir / f"{key}.json"
        if cache_file.exists():
            try:
                with open(cache_file) as f:
                    data = json.load(f)
                # Check if cache is still valid (skill files unchanged)
                if self._is_cache_valid(data):
                    return data
            except:
                pass
        return None
    
    def set_cached_init(self, key: str, data: Dict[str, Any]) -> None:
        """Cache initialization data."""
        cache_file = self.cache_dir / f"{key}.json"
        data["_cache_hash"] = self._compute_skill_hash()
        with open(cache_file, "w") as f:
            json.dump(data, f)
    
    def _compute_skill_hash(self) -> str:
        """Compute hash of skill files for cache invalidation."""
        hasher = hashlib.md5()
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
            "skip_preflight": True,
            "default_pattern": "A",
            "max_agents": 1,
            "context_levels": ["L0", "L1", "L2"],
            "verification": "basic",
            "state_persistence": "minimal"
        }


class BootstrapCache:
    """Cache for bootstrap initialization across session turns."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.cache_file = self.project_root / ".memory" / "ultimate-dev" / "bootstrap_cache.json"
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
    
    def get(self) -> Optional[Dict[str, Any]]:
        """Get cached bootstrap data."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file) as f:
                    data = json.load(f)
                if self._is_valid(data):
                    return data
            except:
                pass
        return None
    
    def set(self, data: Dict[str, Any]) -> None:
        """Set bootstrap cache."""
        data["_skill_hash"] = self._compute_skill_hash()
        data["_timestamp"] = os.path.getmtime(self.project_root / "VERSION")
        with open(self.cache_file, "w") as f:
            json.dump(data, f)
    
    def _compute_skill_hash(self) -> str:
        hasher = hashlib.md5()
        for skill_file in ["SKILL.md", "AGENTS.md", "VERSION"]:
            path = self.project_root / skill_file
            if path.exists():
                hasher.update(path.read_bytes())
        return hasher.hexdigest()
    
    def _is_valid(self, data: Dict) -> bool:
        return (data.get("_skill_hash") == self._compute_skill_hash() and
                data.get("_timestamp") == os.path.getmtime(self.project_root / "VERSION"))
    
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