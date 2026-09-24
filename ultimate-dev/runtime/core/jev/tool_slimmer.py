"""
Jev Tool Slimmer - Context Slimming
Prunes tool schemas based on routing decision and risk level.
"""
from __future__ import annotations
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any

from .types import RoutingTarget, JevAggregatedDecision


@dataclass
class SlimmingResult:
    pruned_tools: List[str] = field(default_factory=list)
    retained_tools: List[str] = field(default_factory=list)
    slimming_reason: str = ""
    slimming_confidence: float = 0.0


class ToolSlimmer:
    """
    Tool Slimmer - Prunes tool schemas based on routing decision and risk.
    Reduces context size by removing irrelevant tools.
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.slimming_threshold = self.config.get("slimming_threshold", 0.75)

        # Tool categories for slimming
        self.tool_categories = {
            "execution": ["run_shell_command", "execute_code", "run_command"],
            "filesystem": ["read_file", "write_file", "edit_file", "glob", "list_directory"],
            "search": ["grep_search", "search_web", "search_code"],
            "git": ["git_diff", "git_status", "git_log", "git_commit"],
            "browser": ["browser_navigate", "browser_click", "browser_type"],
            "api": ["api_request", "http_request", "graphql_query"],
            "database": ["db_query", "db_migrate", "db_execute"],
            "analysis": ["analyze_code", "lint_code", "type_check", "security_scan"],
        }

    def slim(self, tools: List[Dict], agg_decision: 'JevAggregatedDecision') -> List[Dict]:
        """
        Slim tool list based on routing decision and risk.
        Returns pruned tool list.
        """
        if not tools:
            return tools

        routing = getattr(decision, 'routing_target', 'backend')
        risk_level = getattr(decision, 'risk_flags', [])

        if routing == "execute_tool":
            return self._slim_for_execution(tools)
        elif routing == "lightweight_backend":
            return self._slim_for_lightweight(tools)
        elif routing == "human_review":
            return self._slim_for_review(tools)
        elif routing == "flagship_llm":
            return tools  # Full toolset for flagship
        else:
            return self._slim_for_backend(tools)

    def _slim_for_execution(self, tools: List[Dict], agg) -> List[Dict]:
        """Aggressive slimming for direct tool execution."""
        # Keep only execution and directly relevant tools
        relevant_categories = {"execution", "filesystem"}
        return self._filter_by_categories(tools, relevant_categories)

    def _slim_for_lightweight(self, tools: List[Dict], agg) -> List[Dict]:
        """Moderate slimming for lightweight backend."""
        relevant_categories = {"execution", "filesystem", "search", "analysis"}
        return self._filter_by_categories(tools, relevant_categories)

    def _slim_for_backend(self, tools: List[Dict], agg) -> List[Dict]:
        """Standard slimming for backend."""
        relevant_categories = {"execution", "filesystem", "search", "git", "analysis"}
        return self._filter_by_categories(tools, relevant_categories)

    def _slim_for_review(self, tools: List[Dict], agg) -> List[Dict]:
        """Minimal tools for human review - read-only."""
        relevant_categories = {"filesystem", "search", "analysis"}
        return self._filter_by_categories(tools, relevant_categories)

    def _filter_by_categories(self, tools: List[Dict], allowed_categories: set) -> List[Dict]:
        """Filter tools by allowed categories."""
        if not allowed_categories:
            return tools

        pruned = []
        removed = []

        for tool in tools:
            tool_name = tool.get("name", "").lower()
            tool_category = self._categorize_tool(tool_name)

            if tool_category in allowed_categories or tool_category == "unknown":
                pruned.append(tool)
            else:
                removed.append(tool_name)

        return pruned

    def _categorize_tool(self, tool_name: str) -> str:
        """Categorize tool by name."""
        for category, tools in self.tool_categories.items():
            if any(t in tool_name for t in tools):
                return category
        return "unknown"

    def get_slimming_stats(self, original: List[Dict], pruned: List[Dict]) -> Dict:
        """Get slimming statistics."""
        return {
            "original_count": len(original),
            "pruned_count": len(pruned),
            "removed_count": len(original) - len(pruned),
            "reduction_pct": round((1 - len(pruned) / len(original)) * 100, 1) if original else 0
        }


class ToolSlimmerAdvanced:
    """Advanced tool slimmer with semantic matching."""

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.semantic_threshold = self.config.get("semantic_threshold", 0.7)

    def slim_with_semantics(self, tools: List[Dict], task: str, decision) -> List[Dict]:
        """Semantic-aware tool slimming based on task relevance."""
        # For now, delegate to basic slimmer
        basic_slimmer = ToolSlimmer(self.config)
        return basic_slimmer.slim(tools, decision)

    def get_tool_relevance(self, tool: Dict, task: str) -> float:
        """Calculate semantic relevance of tool to task."""
        tool_name = tool.get("name", "").lower()
        tool_desc = tool.get("description", "").lower()
        task_lower = task.lower()

        # Simple keyword overlap scoring
        task_words = set(task_lower.split())
        tool_words = set(tool_name.split() + tool_desc.split())

        overlap = len(task_words & tool_words)
        total = len(task_words | tool_words)

        return overlap / total if total > 0 else 0.0


def create_tool_slimmer(config: Optional[Dict] = None) -> ToolSlimmer:
    return ToolSlimmer(config)


def create_advanced_slimmer(config: Optional[Dict] = None) -> ToolSlimmerAdvanced:
    return ToolSlimmerAdvanced(config)