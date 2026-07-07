"""
End-to-end tests for the CLI, running `python -m sim` as a subprocess.

Responsibilities:
- Verify the acceptance criterion: `python -m sim` runs with no external
  dependencies and prints mean response time and makespan.
- Verify that hitting the tick cap reports a clear error, never partial
  metrics.
"""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    """Runs `python -m sim` with the given CLI args from the repo root."""
    return subprocess.run(
        [sys.executable, "-m", "sim", *args],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )


def test_python_m_sim_prints_metrics() -> None:
    result = run_cli()

    assert result.returncode == 0
    assert "mean response time" in result.stdout
    assert "makespan" in result.stdout


def test_python_m_sim_prints_all_five_canonical_metrics() -> None:
    result = run_cli()

    assert result.returncode == 0
    assert "mean response time" in result.stdout
    assert "mean wait" in result.stdout
    assert "split" in result.stdout
    assert "utilization" in result.stdout
    assert "makespan" in result.stdout


def test_seed_and_ticks_flags_are_accepted() -> None:
    result = run_cli("--seed", "42", "--ticks", "1000")

    assert result.returncode == 0


def test_strategy_edgefirst_runs_and_prints_metrics() -> None:
    result = run_cli("--strategy", "edgefirst")

    assert result.returncode == 0
    assert "EdgeFirst" in result.stdout
    assert "mean response time" in result.stdout
    assert "makespan" in result.stdout


def test_strategy_leastloaded_runs_and_prints_metrics() -> None:
    result = run_cli("--strategy", "leastloaded")

    assert result.returncode == 0
    assert "LeastLoaded" in result.stdout
    assert "mean response time" in result.stdout
    assert "makespan" in result.stdout


def test_tick_cap_overflow_reports_error_not_partial_metrics() -> None:
    result = run_cli("--ticks", "1")

    assert result.returncode != 0
    assert "tick limit" in result.stderr
    assert "mean response time" not in result.stdout
    assert "makespan" not in result.stdout
