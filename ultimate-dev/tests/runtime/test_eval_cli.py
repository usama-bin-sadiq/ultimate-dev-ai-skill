import json
import subprocess
import sys
from pathlib import Path


def test_eval_cli_no_provider_is_honest(tmp_path):
    output = tmp_path / "result.json"
    completed = subprocess.run(
        [sys.executable, "-m", "runtime.eval_cli", "--output", str(output)],
        cwd=Path(__file__).resolve().parents[2],
        env={"PYTHONPATH": str(Path(__file__).resolve().parents[2])},
        check=True,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0
    result = json.loads(output.read_text())
    assert result["mode"] == "no_provider"
    assert result["status"] == "not_run"
