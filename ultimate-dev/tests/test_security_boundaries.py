"""Focused regressions for release/security boundaries owned by this slice."""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = REPO_ROOT / "ultimate-dev"
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))


def test_workflow_shell_blocks_do_not_expand_github_expressions():
    script = PACKAGE_ROOT / "scripts" / "validate-workflows.sh"
    result = subprocess.run(
        ["bash", str(script)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_legacy_jev_entrypoints_fail_closed():
    from runtime.core import jev

    constructors = (
        jev.NOULClassifier,
        jev.ChoiceClassifier,
        jev.ScoreClassifier,
        jev.DeterministicAggregator,
        jev.Guardrails,
        jev.PathRouter,
        jev.ToolSlimmer,
        jev.JevCore,
    )
    for constructor in constructors:
        with pytest.raises(jev.LegacyUnavailableError) as error:
            constructor()
        assert error.value.code == "legacy_unavailable"

    with pytest.raises(jev.LegacyUnavailableError):
        jev.create_jev_core()
    with pytest.raises(jev.LegacyUnavailableError):
        jev.create_guardrails()
    with pytest.raises(jev.LegacyUnavailableError):
        jev.create_path_router()
    with pytest.raises(jev.LegacyUnavailableError):
        jev.create_tool_slimmer()
    with pytest.raises(jev.LegacyUnavailableError):
        jev.JevInput("x", {}, [])
    with pytest.raises(jev.LegacyUnavailableError):
        jev.JevContext(
            user_input="x",
            langchain_state={},
            available_tools=[],
            session_config={},
            project_root=".",
        )


def test_dependency_manager_never_reaches_installation(monkeypatch):
    from runtime.core.sandbox import dependency_manager as module

    with pytest.raises(module.LegacyUnavailableError) as error:
        module.SandboxDependencyManager()
    assert error.value.code == "legacy_unavailable"

    manager = module.SandboxDependencyManager(unsafe_development=True)

    def fail_subprocess(*args, **kwargs):
        raise AssertionError("installation reached subprocess")

    monkeypatch.setattr(module.subprocess, "run", fail_subprocess)
    with pytest.raises(module.UnsafeDevelopmentError) as error:
        manager.install_dependency("docker")
    assert error.value.code == "unsafe-development"

    source = (PACKAGE_ROOT / "runtime/core/sandbox/dependency_manager.py").read_text()
    assert "shell=True" not in source
    assert 'sandbox_local"] = False' in source


def test_posix_installer_is_staged_idempotent_and_refuses_memory_deletion():
    import tempfile

    installer = PACKAGE_ROOT / "scripts" / "install.sh"
    with tempfile.TemporaryDirectory(prefix="ultimate-dev-install-") as directory:
        project = Path(directory)
        (project / ".gitignore").write_text("sentinel-entry\n", encoding="utf-8")
        for _ in range(2):
            result = subprocess.run(
                [str(installer), "--project", str(project), "--yes"],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            assert result.returncode == 0, result.stdout + result.stderr

        target = project / ".agents" / "skills" / "ultimate-dev"
        expected_version = (REPO_ROOT / "VERSION").read_text().strip()
        assert (target / "VERSION").read_text().strip() == expected_version
        assert (target / "SKILL.md").is_file()
        assert not (target / "ultimate-dev").exists()
        assert not (target / "runtime/core/browser/automation.py").exists()
        assert not (target / "runtime/core/sandbox/runner.py").exists()
        assert not (target / "runtime/core/jev/bridge.py").exists()
        assert not (project / ".memory").exists()
        assert (project / ".gitignore").read_text(encoding="utf-8") == "sentinel-entry\n"
        assert not (project / "AGENTS.md").exists()
        assert not (project / "CLAUDE.md").exists()
        assert not (project / ".cursor").exists()
        assert not (project / ".claude").exists()
        assert not any(path.is_symlink() for path in target.rglob("*"))

        result = subprocess.run(
            [str(installer), "--project", str(project), "--clean-memory", "--yes"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode != 0
        assert "memory deletion is disabled" in result.stderr
        assert not (project / ".memory").exists()


def test_posix_uninstall_preserves_nonempty_project_memory():
    import tempfile

    installer = PACKAGE_ROOT / "scripts" / "install.sh"
    with tempfile.TemporaryDirectory(prefix="ultimate-dev-memory-") as directory:
        project = Path(directory)
        memory = project / ".memory" / "ultimate-dev"
        memory.mkdir(parents=True)
        keep = memory / "keep.txt"
        keep.write_text("user data\n", encoding="utf-8")
        install = subprocess.run(
            [str(installer), "--project", str(project), "--yes"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert install.returncode == 0, install.stdout + install.stderr
        assert keep.read_text(encoding="utf-8") == "user data\n"
        uninstall = subprocess.run(
            [str(installer), "--project", str(project), "--uninstall", "--yes"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert uninstall.returncode == 0, uninstall.stdout + uninstall.stderr
        assert keep.is_file()
        assert keep.read_text(encoding="utf-8") == "user data\n"
        refused = subprocess.run(
            [str(installer), "--project", str(project), "--clean-memory", "--yes"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert refused.returncode != 0
        assert "memory deletion is disabled" in refused.stderr
        assert keep.read_text(encoding="utf-8") == "user data\n"


def test_posix_installer_refuses_symlinked_install_parent():
    import tempfile

    installer = PACKAGE_ROOT / "scripts" / "install.sh"
    with tempfile.TemporaryDirectory(prefix="ultimate-dev-symlink-") as directory:
        root = Path(directory)
        project = root / "project"
        outside = root / "outside"
        project.mkdir()
        outside.mkdir()
        try:
            (project / ".agents").symlink_to(outside, target_is_directory=True)
        except OSError:
            pytest.skip("symlinks are unavailable")
        result = subprocess.run(
            [str(installer), "--project", str(project), "--yes"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode != 0
        assert "symlinked install path" in result.stderr
        assert not any(outside.iterdir())


def test_posix_installer_ignores_existing_claude_symlink():
    import tempfile

    installer = PACKAGE_ROOT / "scripts" / "install.sh"
    with tempfile.TemporaryDirectory(prefix="ultimate-dev-claude-link-") as directory:
        root = Path(directory)
        project = root / "project"
        outside = root / "outside"
        project.mkdir()
        outside.mkdir()
        (project / ".claude" / "skills").mkdir(parents=True)
        link = project / ".claude" / "skills" / "ultimate-dev"
        try:
            link.symlink_to(outside, target_is_directory=True)
        except OSError:
            pytest.skip("symlinks are unavailable")
        result = subprocess.run(
            [str(installer), "--project", str(project), "--yes"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert link.is_symlink()
        assert not (project / ".memory").exists()
        assert not (project / ".gitignore").exists()
        assert not (project / ".cursor").exists()
        assert not (project / "AGENTS.md").exists()
        assert not (project / "CLAUDE.md").exists()


def test_posix_installer_is_interactive_and_copy_only():
    import tempfile

    installer = PACKAGE_ROOT / "scripts" / "install.sh"
    with tempfile.TemporaryDirectory(prefix="ultimate-dev-interactive-") as directory:
        project = Path(directory)
        result = subprocess.run(
            [str(installer)],
            cwd=REPO_ROOT,
            input=f"2\n2\n{project}\ny\n",
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        target = project / ".agents" / "skills" / "ultimate-dev"
        assert (target / "SKILL.md").is_file()
        assert (target / "contracts" / "task-envelope.yaml").is_file()
        assert (target / "skills" / "universal-task" / "SKILL.md").is_file()
        assert not any(path.name in {"__pycache__", ".pytest_cache", ".DS_Store"} for path in target.rglob("*"))
        assert not list(target.rglob("*.pyc"))
        assert "Payload size:" in result.stdout
        assert not (project / ".memory").exists()
        assert not (project / ".gitignore").exists()
        assert not (project / "AGENTS.md").exists()
        assert not (project / "CLAUDE.md").exists()
        assert not (project / ".cursor").exists()
        assert not (project / ".claude").exists()


def test_posix_tool_specific_menu_selects_native_destination():
    import tempfile

    installer = PACKAGE_ROOT / "scripts" / "install.sh"
    with tempfile.TemporaryDirectory(prefix="ultimate-dev-tool-menu-") as directory:
        project = Path(directory) / "project"
        project.mkdir()
        result = subprocess.run(
            [str(installer)],
            cwd=REPO_ROOT,
            input=f"1\n1\n2\n{project}\ny\n",
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert (project / ".claude" / "skills" / "ultimate-dev" / "SKILL.md").is_file()
        assert not (project / ".agents").exists()


def test_powershell_installer_contains_copy_only_guards():
    source = (PACKAGE_ROOT / "scripts" / "install.ps1").read_text(encoding="utf-8")
    assert "Join-Path $RepoRoot 'VERSION'" in source
    assert "Move-Item -LiteralPath $stage -Destination $target" in source
    assert "Memory deletion is disabled" in source
    assert "Remove-Item -LiteralPath $memoryDir" not in source
    assert "Ensure-MemoryScaffolding" not in source
    assert "SymbolicLink" not in source
    assert "runtime/core/browser/automation.py" in source
    assert "runtime/core/sandbox/runner.py" in source
    assert "runtime/core/jev/bridge.py" in source
    assert "__pycache__" in source
    assert ".pytest_cache" in source
    assert "Payload size:" in source


def test_powershell_installer_is_staged_and_idempotent_when_available():
    import tempfile

    powershell = shutil.which("pwsh-preview") or shutil.which("pwsh")
    if not powershell:
        pytest.skip("PowerShell is not available")
    installer = PACKAGE_ROOT / "scripts" / "install.ps1"
    with tempfile.TemporaryDirectory(prefix="ultimate-dev-pwsh-install-") as directory:
        project = Path(directory)
        (project / ".gitignore").write_text("sentinel-entry\n", encoding="utf-8")
        memory = project / ".memory" / "ultimate-dev"
        memory.mkdir(parents=True)
        keep = memory / "keep.txt"
        keep.write_text("user data\n", encoding="utf-8")
        for _ in range(2):
            result = subprocess.run(
                [powershell, "-NoLogo", "-NoProfile", "-File", str(installer), "-Project", str(project), "-Yes"],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            assert result.returncode == 0, result.stdout + result.stderr
        target = project / ".agents" / "skills" / "ultimate-dev"
        assert (target / "VERSION").read_text().strip() == (REPO_ROOT / "VERSION").read_text().strip()
        assert (target / "SKILL.md").is_file()
        assert not (target / "ultimate-dev").exists()
        assert not (target / "runtime/core/browser/automation.py").exists()
        assert keep.read_text(encoding="utf-8") == "user data\n"
        assert (project / ".gitignore").read_text(encoding="utf-8") == "sentinel-entry\n"
        assert not (project / "AGENTS.md").exists()
        assert not (project / "CLAUDE.md").exists()
        assert not (project / ".cursor").exists()
        assert not (project / ".claude").exists()
        assert not any(path.is_symlink() for path in target.rglob("*"))
        result = subprocess.run(
            [powershell, "-NoLogo", "-NoProfile", "-File", str(installer), "-Project", str(project), "-CleanMemory", "-Yes"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode != 0
        assert "Memory deletion is disabled" in result.stderr
        uninstall = subprocess.run(
            [powershell, "-NoLogo", "-NoProfile", "-File", str(installer), "-Project", str(project), "-Uninstall", "-Yes"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert uninstall.returncode == 0, uninstall.stdout + uninstall.stderr
        assert keep.read_text(encoding="utf-8") == "user data\n"
        assert not target.exists()


def test_powershell_installer_ignores_existing_claude_symlink_when_available():
    import tempfile

    powershell = shutil.which("pwsh-preview") or shutil.which("pwsh")
    if not powershell:
        pytest.skip("PowerShell is not available")
    installer = PACKAGE_ROOT / "scripts" / "install.ps1"
    with tempfile.TemporaryDirectory(prefix="ultimate-dev-pwsh-claude-link-") as directory:
        root = Path(directory)
        project = root / "project"
        outside = root / "outside"
        project.mkdir()
        outside.mkdir()
        (project / ".claude" / "skills").mkdir(parents=True)
        link = project / ".claude" / "skills" / "ultimate-dev"
        try:
            link.symlink_to(outside, target_is_directory=True)
        except OSError:
            pytest.skip("symlinks are unavailable")
        result = subprocess.run(
            [powershell, "-NoLogo", "-NoProfile", "-File", str(installer), "-Project", str(project), "-Yes"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert link.is_symlink()
        assert not (project / ".memory").exists()
        assert not (project / ".gitignore").exists()
        assert not (project / ".cursor").exists()
        assert not (project / "AGENTS.md").exists()
        assert not (project / "CLAUDE.md").exists()


def test_powershell_installer_is_interactive_and_copy_only_when_available():
    import tempfile

    powershell = shutil.which("pwsh-preview") or shutil.which("pwsh")
    if not powershell:
        pytest.skip("PowerShell is not available")
    installer = PACKAGE_ROOT / "scripts" / "install.ps1"
    with tempfile.TemporaryDirectory(prefix="ultimate-dev-pwsh-interactive-") as directory:
        project = Path(directory)
        result = subprocess.run(
            [powershell, "-NoLogo", "-NoProfile", "-File", str(installer)],
            cwd=REPO_ROOT,
            input=f"2\n2\n{project}\ny\n",
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        target = project / ".agents" / "skills" / "ultimate-dev"
        assert (target / "SKILL.md").is_file()
        assert (target / "contracts" / "task-envelope.yaml").is_file()
        assert (target / "skills" / "universal-task" / "SKILL.md").is_file()
        assert not any(path.name in {"__pycache__", ".pytest_cache", ".DS_Store"} for path in target.rglob("*"))
        assert not list(target.rglob("*.pyc"))
        assert "Payload size:" in result.stdout
        assert not (project / ".memory").exists()
        assert not (project / ".gitignore").exists()
        assert not (project / "AGENTS.md").exists()
        assert not (project / "CLAUDE.md").exists()
        assert not (project / ".cursor").exists()
        assert not (project / ".claude").exists()


def test_powershell_tool_specific_menu_selects_native_destination_when_available():
    import tempfile

    powershell = shutil.which("pwsh-preview") or shutil.which("pwsh")
    if not powershell:
        pytest.skip("PowerShell is not available")
    installer = PACKAGE_ROOT / "scripts" / "install.ps1"
    with tempfile.TemporaryDirectory(prefix="ultimate-dev-pwsh-tool-menu-") as directory:
        project = Path(directory) / "project"
        project.mkdir()
        result = subprocess.run(
            [powershell, "-NoLogo", "-NoProfile", "-File", str(installer)],
            cwd=REPO_ROOT,
            input=f"1\n1\n2\n{project}\ny\n",
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert (project / ".claude" / "skills" / "ultimate-dev" / "SKILL.md").is_file()
        assert not (project / ".agents").exists()


def test_workflow_files_have_explicit_permissions_and_concurrency():
    for path in sorted((REPO_ROOT / ".github/workflows").glob("*.yml")):
        text = path.read_text(encoding="utf-8")
        assert "permissions:" in text, path
        assert "concurrency:" in text, path
        # A useful cheap guard against reintroducing the original injection
        # pattern in an inline command.
        assert not any(
            line.strip().startswith("run:") and "${{" in line
            for line in text.splitlines()
        )
