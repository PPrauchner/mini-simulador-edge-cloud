"""
Integration tests for the discrete-time engine via `engine.run(scenario, strategy)`.

Responsibilities:
- Verify observable metrics (Monitor) against hand-calculated values.
- Verify engine invariants: capacity never exceeded, every Task reaches DONE.
- Verify failure modes: tick-limit overflow and fail-fast Scenario validation.
"""

import pytest

from sim.engine import TickLimitExceededError, run
from sim.model import Scenario, Server, ServerVariety, Task, TaskState
from sim.strategies import AllCloud


def test_response_time_and_makespan_hand_calculated() -> None:
    # Cloud with capacity 1 forces the second Task to wait.
    cloud = Server(name="cloud", variety=ServerVariety.CLOUD, capacity=1)
    first = Task(arrival=0, origin="edge-a", duration=2)
    second = Task(arrival=0, origin="edge-a", duration=3)
    scenario = Scenario(servers=[cloud], tasks=[first, second])

    monitor = run(scenario, AllCloud())

    # first:  runs ticks 0-1 -> wait 0 + latency 8 + duration 2 = 10
    # second: slot frees at end of tick 1, allocated at tick 2, runs 2-4
    #         -> wait 2 + latency 8 + duration 3 = 13
    assert monitor.mean_response_time == pytest.approx((10 + 13) / 2)
    assert monitor.makespan == 4


def test_capacity_never_exceeded_and_every_task_done() -> None:
    # Contended cloud (capacity 3) under a staggered load of mixed demands.
    scenario = Scenario(
        servers=[
            Server(name="edge-a", variety=ServerVariety.EDGE, capacity=2, site="edge-a"),
            Server(name="cloud", variety=ServerVariety.CLOUD, capacity=3),
        ],
        tasks=[
            Task(arrival=0, origin="edge-a", duration=2, demand=2),
            Task(arrival=0, origin="edge-a", duration=3, demand=2),
            Task(arrival=1, origin="edge-a", duration=1),
            Task(arrival=2, origin="edge-a", duration=2, demand=3),
            Task(arrival=3, origin="edge-a", duration=4),
        ],
    )

    monitor = run(scenario, AllCloud())

    capacity = {server.name: server.capacity for server in scenario.servers}
    for tick_occupancy in monitor.occupancy:
        for name, used in tick_occupancy.items():
            assert used <= capacity[name]
    assert all(task.state is TaskState.DONE for task in scenario.tasks)


def test_homogeneous_load_completes_every_task() -> None:
    # Identical Tasks must be treated as distinct individuals by the queue.
    cloud = Server(name="cloud", variety=ServerVariety.CLOUD, capacity=2)
    tasks = [Task(arrival=0, origin="edge-a", duration=2) for _ in range(4)]
    scenario = Scenario(servers=[cloud], tasks=tasks)

    monitor = run(scenario, AllCloud())

    assert all(task.state is TaskState.DONE for task in tasks)
    # two run ticks 0-1 (wait 0), two run ticks 2-3 (wait 2); latency 8
    assert monitor.mean_response_time == pytest.approx((10 + 10 + 12 + 12) / 4)
    assert monitor.makespan == 3


def test_exceeding_tick_limit_fails_with_clear_message() -> None:
    cloud = Server(name="cloud", variety=ServerVariety.CLOUD, capacity=1)
    scenario = Scenario(
        servers=[cloud],
        tasks=[Task(arrival=0, origin="edge-a", duration=5)],
    )

    with pytest.raises(TickLimitExceededError, match=r"3.*1 task"):
        run(scenario, AllCloud(), max_ticks=3)


def test_task_that_fits_no_server_fails_before_simulating() -> None:
    class CountingAllCloud(AllCloud):
        """AllCloud that counts place() calls, to prove none happened."""

        def __init__(self) -> None:
            self.calls = 0

        def place(self, pending: list[Task], servers: list[Server]) -> list[tuple[Task, Server | None]]:
            self.calls += 1
            return super().place(pending, servers)

    scenario = Scenario(
        servers=[
            Server(name="edge-a", variety=ServerVariety.EDGE, capacity=2, site="edge-a"),
            Server(name="cloud", variety=ServerVariety.CLOUD, capacity=3),
        ],
        tasks=[Task(arrival=0, origin="edge-a", duration=1, demand=4)],
    )
    strategy = CountingAllCloud()

    with pytest.raises(ValueError, match=r"demand 4.*max capacity 3"):
        run(scenario, strategy)
    assert strategy.calls == 0
