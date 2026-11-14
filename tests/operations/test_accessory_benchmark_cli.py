"""The diagnostic command must expose help and reject unsupported flags."""

import json
import os
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "tools" / "benchmark_accessory_context.py"
ENV = {**os.environ, "PYTHONPATH": str(SCRIPT.parents[1] / "src")}


def test_benchmark_help_does_not_run_measurements(tmp_path):
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=ENV,
    )
    assert result.returncode == 0
    assert "usage:" in result.stdout
    assert "median_seconds" not in result.stdout


def test_benchmark_unknown_flag_is_rejected(tmp_path):
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--unsupported"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=ENV,
    )
    assert result.returncode == 2
    assert "unrecognized arguments" in result.stderr
    assert "median_seconds" not in result.stdout


def test_benchmark_default_retains_json_and_explicit_counts(tmp_path):
    result = subprocess.run(
        [sys.executable, str(SCRIPT)], cwd=tmp_path, capture_output=True, text=True, env=ENV
    )
    assert result.returncode == 0
    rows = json.loads(result.stdout)
    assert [r["characters"] for r in rows] == [1000, 5000, 10000, 20000]
    assert all(
        r["accessory_mentions"] > 0 and r["repetitions"] == len(r["seconds"]) == 3 for r in rows
    )
