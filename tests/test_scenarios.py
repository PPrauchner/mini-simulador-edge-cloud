"""
Tests for the parameterized Scenario factories (low/high load).

Responsibilities:
- Verify reproducibility: same seed + same params -> same load and metrics.
- Verify seed variation: different seeds -> different loads.
- Verify that the high-load preset produces observable contention.
"""

from sim.engine import run
from sim.scenarios import make_scenario
from sim.strategies import AllCloud


def _signatures(scenario) -> list[tuple[int, str, int, int]]:
    """Task fields that define a load, order-independent."""
    return sorted(
        (t.arrival, t.origin, t.duration, t.demand) for t in scenario.tasks
    )


def test_high_load_is_reproducible_for_same_seed() -> None:
    first = make_scenario("high", seed=7)
    second = make_scenario("high", seed=7)

    monitor_first = run(first, AllCloud())
    monitor_second = run(second, AllCloud())

    assert _signatures(first) == _signatures(second)
    assert monitor_first.mean_wait == monitor_second.mean_wait
    assert monitor_first.mean_response_time == monitor_second.mean_response_time
    assert monitor_first.makespan == monitor_second.makespan


def test_different_seeds_produce_different_loads() -> None:
    one = make_scenario("high", seed=1)
    two = make_scenario("high", seed=2)

    assert _signatures(one) != _signatures(two)


def test_high_load_shows_contention() -> None:
    high = make_scenario("high", seed=0)

    monitor = run(high, AllCloud())

    # Contention manifests as Tasks waiting PENDING before they are placed.
    assert monitor.mean_wait > 0


def test_low_load_waits_less_than_high_load() -> None:
    low = make_scenario("low", seed=0)
    high = make_scenario("high", seed=0)

    low_wait = run(low, AllCloud()).mean_wait
    high_wait = run(high, AllCloud()).mean_wait

    assert low_wait < high_wait
