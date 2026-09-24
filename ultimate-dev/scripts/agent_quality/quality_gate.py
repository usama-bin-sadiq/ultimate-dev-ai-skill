#!/usr/bin/env python3
"""
Agent Quality Gate — Ensures all agents meet minimum quality standards.
"""
import os
import re
import yaml
from pathlib import Path
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass, field


@dataclass
class AgentQualityReport:
    """Report for a single agent."""
    path: str
    name: str
    domain: str
    passed: bool
    score: int  # 0-100
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class AgentQualityGate:
    """Validates agent quality against minimum standards."""
    
    # Minimum requirements
    REQUIRED_FRONTMATTER_FIELDS = [
        "name", "domain", "description", "triggers", "anti_triggers"
    ]
    
    MIN_CONTENT_LINES = 15
    MIN_DESCRIPTION_WORDS = 15
    MIN_TRIGGERS = 2
    MIN_ANTI_TRIGGERS = 1
    
    # Required sections in agent body
    REQUIRED_SECTIONS = [
        "overview", "capabilities", "usage"
    ]
    
    def __init__(self, agents_dir: str):
        self.agents_dir = Path(agents_dir).resolve()
        self.base_dir = self.agents_dir.parent
        self.reports: List[AgentQualityReport] = []
    
    def validate_all(self) -> Dict[str, Any]:
        """Validate all agents in directory."""
        self.reports = []
        
        for agent_file in self.agents_dir.rglob("*.md"):
            if "_shared" in str(agent_file):
                continue
            if agent_file.name.startswith("."):
                continue
            
            # Calculate relative path from base_dir
            try:
                rel_path = str(agent_file.relative_to(self.base_dir))
            except ValueError:
                rel_path = str(agent_file)
            
            report = self._validate_agent(agent_file, rel_path)
            self.reports.append(report)
        
        return self._generate_summary()
    
    def _validate_agent(self, agent_file: Path, rel_path: str) -> AgentQualityReport:
        """Validate a single agent file."""
        content = agent_file.read_text()
        
        # Parse frontmatter
        fm_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        frontmatter = {}
        if fm_match:
            try:
                frontmatter = yaml.safe_load(fm_match.group(1)) or {}
            except:
                pass
        
        name = frontmatter.get("name", agent_file.stem)
        domain = frontmatter.get("domain", "unknown")
        
        issues = []
        warnings = []
        score = 100
        
        # Check required frontmatter fields
        for field in self.REQUIRED_FRONTMATTER_FIELDS:
            if field not in frontmatter or not frontmatter[field]:
                issues.append(f"Missing required frontmatter field: {field}")
                score -= 15
        
        # Check triggers
        triggers = frontmatter.get("triggers", [])
        if len(triggers) < self.MIN_TRIGGERS:
            issues.append(f"Too few triggers ({len(triggers)} < {self.MIN_TRIGGERS})")
            score -= 10
        
        # Check anti_triggers
        anti_triggers = frontmatter.get("anti_triggers", [])
        if len(anti_triggers) < self.MIN_ANTI_TRIGGERS:
            issues.append(f"Too few anti_triggers ({len(anti_triggers)} < {self.MIN_ANTI_TRIGGERS})")
            score -= 10
        
        # Check description quality
        description = frontmatter.get("description", "")
        word_count = len(description.split())
        if word_count < self.MIN_DESCRIPTION_WORDS:
            warnings.append(f"Description too short ({word_count} words < {self.MIN_DESCRIPTION_WORDS})")
            score -= 5
        
        # Check body content
        body = content[fm_match.end():] if fm_match else content
        body_lines = [l for l in body.split('\n') if l.strip() and not l.startswith('#')]
        
        if len(body_lines) < self.MIN_CONTENT_LINES:
            issues.append(f"Body content too short ({len(body_lines)} lines < {self.MIN_CONTENT_LINES})")
            score -= 10
        
        # Check for required sections (case-insensitive)
        body_lower = body.lower()
        for section in self.REQUIRED_SECTIONS:
            if section.lower() not in body_lower:
                warnings.append(f"Missing recommended section: {section}")
                score -= 3
        
        # Check for examples
        if "example" not in body_lower and "usage" not in body_lower:
            warnings.append("No usage examples found")
            score -= 5
        
        # Check for specific capability details
        if "capabilit" not in body_lower and "skill" not in body_lower:
            warnings.append("No capabilities/skills section")
            score -= 3
        
        # Check for anti-patterns
        if "spawn" in body_lower and "agent" in body_lower:
            if "inline" not in body_lower and "subagent" not in body_lower:
                warnings.append("May claim to spawn agents without clarifying execution mode")
                score -= 3
        
        score = max(0, score)
        passed = len(issues) == 0 and score >= 60
        
        return AgentQualityReport(
            path=str(agent_file.relative_to(self.agents_dir.parent)),
            name=name,
            domain=domain,
            passed=passed,
            score=score,
            issues=issues,
            warnings=warnings
        )
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate summary report."""
        total = len(self.reports)
        passed = sum(1 for r in self.reports if r.passed)
        failed = total - passed
        avg_score = sum(r.score for r in self.reports) / total if total > 0 else 0
        
        # Domain breakdown
        domains = {}
        for r in self.reports:
            if r.domain not in domains:
                domains[r.domain] = {"total": 0, "passed": 0, "avg_score": 0}
            domains[r.domain]["total"] += 1
            if r.passed:
                domains[r.domain]["passed"] += 1
            domains[r.domain]["avg_score"] = (
                (domains[r.domain]["avg_score"] * (domains[r.domain]["total"] - 1) + r.score) 
                / domains[r.domain]["total"]
            )
        
        return {
            "total_agents": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": passed / total if total > 0 else 0,
            "average_score": avg_score,
            "domains": domains,
            "reports": [
                {
                    "path": r.path,
                    "name": r.name,
                    "domain": r.domain,
                    "passed": r.passed,
                    "score": r.score,
                    "issues": r.issues,
                    "warnings": r.warnings
                }
                for r in self.reports
            ]
        }


def run_quality_gate(agents_dir: str) -> Dict[str, Any]:
    """Run quality gate on agents directory."""
    gate = AgentQualityGate(agents_dir)
    return gate.validate_all()


def print_report(report: Dict[str, Any]) -> None:
    """Print formatted report."""
    print("=" * 60)
    print("AGENT QUALITY GATE REPORT")
    print("=" * 60)
    print(f"Total Agents: {report['total_agents']}")
    print(f"Passed: {report['passed']} ({report['pass_rate']:.1%})")
    print(f"Failed: {report['failed']}")
    print(f"Average Score: {report['average_score']:.1f}/100")
    print()
    
    print("Domain Breakdown:")
    for domain, stats in sorted(report['domains'].items()):
        print(f"  {domain}: {stats['passed']}/{stats['total']} passed, avg {stats['avg_score']:.1f}")
    print()
    
    # Show failed agents
    failed = [r for r in report['reports'] if not r['passed']]
    if failed:
        print("FAILED AGENTS:")
        for r in failed:
            print(f"  ❌ {r['path']} (score: {r['score']})")
            for issue in r['issues']:
                print(f"    - {issue}")
            for warn in r['warnings']:
                print(f"    ⚠ {warn}")
    else:
        print("✅ ALL AGENTS PASSED")


if __name__ == "__main__":
    import sys
    agents_dir = sys.argv[1] if len(sys.argv) > 1 else "ultimate-dev/agents"
    report = run_quality_gate(agents_dir)
    print_report(report)
    sys.exit(0 if report['failed'] == 0 else 1)