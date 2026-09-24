import json
import subprocess
import sys
from pathlib import Path


def _run(root, *args):
    return subprocess.run(
        [sys.executable, "-m", "runtime.task_admin", "--project-root", str(root), *args],
        cwd=Path(__file__).resolve().parents[2],
        env={"PYTHONPATH": str(Path(__file__).resolve().parents[2])},
        check=True,
        capture_output=True,
        text=True,
    )


def test_task_admin_status_and_safe_cleanup_plan(tmp_path):
    runtime_root = tmp_path
    create = subprocess.run(
        [sys.executable, "-c", "from runtime.core import Runtime; r=Runtime('.'); s=r.start({'goal':'admin'}); print(s['task_id'])"],
        cwd=runtime_root,
        env={"PYTHONPATH": str(Path(__file__).resolve().parents[2])},
        check=True,
        capture_output=True,
        text=True,
    )
    task_id = create.stdout.strip().splitlines()[-1]
    status = json.loads(_run(runtime_root, "status", task_id).stdout)
    assert status["task_id"] == task_id
    health = json.loads(_run(runtime_root, "health", task_id).stdout)
    assert health["healthy"] is True
    plan = json.loads(_run(runtime_root, "cleanup", "--retention", "0d", "--dry-run").stdout)
    assert plan["dry_run"] is True
    assert plan["counts"]["selected"] >= 0


def test_task_admin_dry_run_wins_over_archive_flag(tmp_path):
    runtime_root = tmp_path
    create = subprocess.run(
        [sys.executable, "-c", "from runtime.core import Runtime; r=Runtime('.'); s=r.start({'goal':'admin'}); print(s['task_id'])"],
        cwd=runtime_root,
        env={"PYTHONPATH": str(Path(__file__).resolve().parents[2])},
        check=True,
        capture_output=True,
        text=True,
    )
    task_id = create.stdout.strip().splitlines()[-1]
    task_path = runtime_root / ".memory" / "ultimate-dev" / "tasks" / task_id
    state_path = task_path / "state.json"
    state = json.loads(state_path.read_text())
    state["status"] = "completed"
    state["updated_at"] = "2000-01-01T00:00:00Z"
    state_path.write_text(json.dumps(state))
    archive_root = runtime_root / ".memory" / "ultimate-dev" / "task-archives"
    _run(runtime_root, "cleanup", "--retention", "0d", "--archive", "--dry-run")
    assert task_path.is_dir()
    assert not archive_root.exists()

    archived = json.loads(_run(runtime_root, "cleanup", "--retention", "0d", "--archive").stdout)
    archive_entry = next(item for item in archived["entries"] if item["task_id"] == task_id)
    restored = json.loads(_run(runtime_root, "restore", archive_entry["archive_path"]).stdout)
    assert restored["status"] == "restored"
    assert task_path.is_dir()
