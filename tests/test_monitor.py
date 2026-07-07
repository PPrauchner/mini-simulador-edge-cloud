"""
Unit tests for the Monitor aggregates over a known sequence of records.

Responsibilities:
- Feed the Monitor a hand-built sequence of occupancy snapshots and Task
  completions, then verify each canonical aggregate against values
  calculated by hand.
"""

import pytest

from sim.engine import run
from sim.model import Scenario, Server, ServerVariety, Task
from sim.monitor import Monitor
from sim.strategies import EdgeFirst


def test_mean_wait_averages_pending_ticks() -> None:
    monitor = Monitor()
    monitor.record_completion(
        wait=0, latency=1, duration=2, tick=1, variety=ServerVariety.EDGE
    )
    monitor.record_completion(
        wait=3, latency=8, duration=1, tick=2, variety=ServerVariety.CLOUD
    )

    assert monitor.mean_wait == pytest.approx((0 + 3) / 2)


def test_split_counts_tasks_per_server_variety() -> None:
    monitor = Monitor()
    monitor.record_completion(
        wait=0, latency=1, duration=2, tick=1, variety=ServerVariety.EDGE
    )
    monitor.record_completion(
        wait=0, latency=8, duration=1, tick=1, variety=ServerVariety.CLOUD
    )
    monitor.record_completion(
        wait=1, latency=8, duration=2, tick=2, variety=ServerVariety.CLOUD
    )

    assert monitor.split == {ServerVariety.EDGE: 1, ServerVariety.CLOUD: 2}


def test_mean_utilization_averages_occupancy_over_capacity() -> None:
    monitor = Monitor(capacities={"edge": 2, "cloud": 4})
    monitor.record_occupancy({"edge": 1, "cloud": 2})
    monitor.record_occupancy({"edge": 2, "cloud": 0})

    expected = {"edge": (1 / 2 + 2 / 2) / 2, "cloud": (2 / 4 + 0 / 4) / 2}
    assert monitor.mean_utilization == pytest.approx(expected)


def test_five_metrics_end_to_end_hand_calculated() -> None:
    # Edge (capacity 1) fills, then overflow spills to the cloud (capacity 2),
    # so the split is mixed and every canonical window is exercised.
    scenario = Scenario(
        servers=[
            Server(name="edge-a", variety=ServerVariety.EDGE, capacity=1, site="edge-a"),
            Server(name="cloud", variety=ServerVariety.CLOUD, capacity=2),
        ],
        tasks=[
            Task(arrival=0, origin="edge-a", duration=2),
            Task(arrival=0, origin="edge-a", duration=2),
            Task(arrival=1, origin="edge-a", duration=1),
        ],
    )

    monitor = run(scenario, EdgeFirst())

    # t0: T1 -> edge-a (wait 0). T2 stays PENDING (edge full).
    # t1: T2, T3 -> cloud (wait 0). T1 DONE at t1 on edge (lat 1, dur 2).
    #     T3 DONE at t1 on cloud (lat 8, dur 1).
    # t2: T2 DONE on cloud (allocated t1, arrival 0 -> wait 1, lat 8, dur 2).
    assert monitor.split == {ServerVariety.EDGE: 1, ServerVariety.CLOUD: 2}
    assert monitor.makespan == 2
    assert monitor.mean_wait == pytest.approx((0 + 0 + 1) / 3)
    assert monitor.mean_response_time == pytest.approx(
        ((0 + 1 + 2) + (0 + 8 + 1) + (1 + 8 + 2)) / 3
    )
    # occupancy over ticks 0..makespan (3 ticks): edge-a [1, 1, 0]; cloud [0, 2, 1].
    assert monitor.mean_utilization == pytest.approx(
        {"edge-a": (1 + 1 + 0) / 3, "cloud": (0 + 2 / 2 + 1 / 2) / 3}
    )
