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


def test_scenario_low_runs_and_prints_metrics() -> None:
    result = run_cli("--scenario", "low")

    assert result.returncode == 0
    assert "scenario: low" in result.stdout
    assert "mean wait" in result.stdout


def test_scenario_high_runs_and_prints_metrics() -> None:
    result = run_cli("--scenario", "high")

    assert result.returncode == 0
    assert "scenario: high" in result.stdout
    assert "mean wait" in result.stdout


def test_load_param_overrides_are_accepted() -> None:
    result = run_cli(
        "--scenario",
        "high",
        "--num-tasks",
        "8",
        "--duration-min",
        "1",
        "--duration-max",
        "2",
        "--demand-min",
        "1",
        "--demand-max",
        "1",
        "--arrival-window",
        "20",
    )

    assert result.returncode == 0


def test_same_seed_and_params_are_reproducible_via_cli() -> None:
    args = ("--scenario", "high", "--seed", "5")

    first = run_cli(*args)
    second = run_cli(*args)

    assert first.returncode == 0
    assert first.stdout == second.stdout


def test_compare_prints_a_row_per_strategy_with_the_five_metrics() -> None:
    result = run_cli("--compare")

    assert result.returncode == 0
    assert "AllCloud" in result.stdout
    assert "EdgeFirst" in result.stdout
    assert "LeastLoaded" in result.stdout
    assert "response" in result.stdout
    assert "wait" in result.stdout
    assert "edge/cloud" in result.stdout
    assert "util" in result.stdout
    assert "makespan" in result.stdout


def test_compare_is_reproducible_for_the_same_seed() -> None:
    args = ("--compare", "--scenario", "high", "--seed", "5")

    first = run_cli(*args)
    second = run_cli(*args)

    assert first.returncode == 0
    assert first.stdout == second.stdout


def test_compare_tick_cap_overflow_names_the_failing_strategy() -> None:
    result = run_cli("--scenario", "high", "--ticks", "40", "--compare")

    assert result.returncode != 0
    assert "tick limit" in result.stderr
    assert "AllCloud" in result.stderr


def test_tick_cap_overflow_reports_error_not_partial_metrics() -> None:
    result = run_cli("--ticks", "1")

    assert result.returncode != 0
    assert "tick limit" in result.stderr
    assert "mean response time" not in result.stdout
    assert "makespan" not in result.stdout
