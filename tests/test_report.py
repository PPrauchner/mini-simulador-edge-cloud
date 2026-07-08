"""
Tests for the report module: assembly of the comparison table.

Responsibilities:
- Verify the table has one row per strategy and one column per canonical
  metric, built from each strategy's Monitor.
- Verify the presentation lives in the report module, fed by real runs.
"""

import pytest

from sim.engine import run
from sim.monitor import Monitor
from sim.report import compare_table
from sim.scenarios import make_scenario
from sim.strategies import AllCloud, EdgeFirst, LeastLoaded


def _run_all(scenario_name: str = "minimal") -> list[tuple[str, Monitor]]:
    """Runs the same Scenario under each catalog strategy for the table."""
    catalog = [
        ("AllCloud", AllCloud),
        ("EdgeFirst", EdgeFirst),
        ("LeastLoaded", LeastLoaded),
    ]
    return [(name, run(make_scenario(scenario_name), cls())) for name, cls in catalog]


def test_compare_table_has_a_row_per_strategy() -> None:
    table = compare_table(_run_all())

    assert "AllCloud" in table
    assert "EdgeFirst" in table
    assert "LeastLoaded" in table


def test_all_strategies_see_the_same_load() -> None:
    # A fair comparison: every strategy runs the same Scenario, so each one
    # completes the same number of Tasks (only where they run may differ).
    results = _run_all("high")

    task_counts = {sum(monitor.split.values()) for _, monitor in results}

    assert task_counts == {24}


def test_compare_table_has_the_five_canonical_metric_columns() -> None:
    header = compare_table(_run_all()).splitlines()[0]

    assert "response" in header
    assert "wait" in header
    assert "edge/cloud" in header
    assert "util" in header
    assert "makespan" in header


def test_compare_table_rejects_empty_results() -> None:
    with pytest.raises(ValueError, match="at least one result"):
        compare_table([])


def test_compare_table_rejects_monitors_from_different_scenarios() -> None:
    mismatched_monitor = run(make_scenario("minimal"), AllCloud())
    mismatched_monitor.capacities = {**mismatched_monitor.capacities, "edge-b": 1}

    with pytest.raises(ValueError, match="different Servers"):
        compare_table([("A", _run_all()[0][1]), ("B", mismatched_monitor)])
