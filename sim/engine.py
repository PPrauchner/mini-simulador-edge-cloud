"""
Discrete-time engine: advances the simulation one Tick at a time.

Responsibilities:
- Run the per-Tick loop: arrivals -> placement -> progress -> metrics.
- Own the capacity invariant: validate the feasibility of the batch
  returned by the Placement Strategy (ADR-0001).
- Run to natural termination (every Task DONE), with max_ticks as a
  safety cap that fails loudly instead of reporting partial metrics.
"""

from sim.model import Scenario, Server, Task, TaskState
from sim.monitor import Monitor
from sim.strategies import PlacementStrategy


def _validate(scenario: Scenario) -> None:
    """Fails fast on a Scenario that could never complete.

    Args:
        scenario: Scenario to check before simulating.

    Raises:
        ValueError: If a Task's demand exceeds the capacity of every Server.
    """
    max_capacity = max(server.capacity for server in scenario.servers)
    for task in scenario.tasks:
        if task.demand > max_capacity:
            raise ValueError(
                f"{task} has demand {task.demand}, which exceeds the "
                f"capacity of every Server (max capacity {max_capacity})"
            )


class TickLimitExceededError(RuntimeError):
    """Raised when the safety cap on Ticks is hit before every Task is DONE.

    Partial metrics are never reported as complete: hitting the cap is
    always an error, not a truncated result.
    """


def run(
    scenario: Scenario,
    strategy: PlacementStrategy,
    max_ticks: int = 10_000,
) -> Monitor:
    """Simulates a Scenario under a Placement Strategy until every Task is DONE.

    Args:
        scenario: Infrastructure (Servers) + load (Tasks) to simulate.
        strategy: Placement Strategy that decides where each Task runs.
        max_ticks: Safety cap on simulated Ticks; exceeding it is an error.

    Returns:
        The Monitor with the observed metrics of the complete run.

    Raises:
        ValueError: If a Task's demand exceeds the capacity of every Server
            (fail-fast, before simulating).
        TickLimitExceededError: If max_ticks elapse before every Task is DONE.
    """
    _validate(scenario)
    monitor = Monitor(
        capacities={server.name: server.capacity for server in scenario.servers}
    )
    pending: list[Task] = []
    running: list[tuple[Task, Server]] = []

    for tick in range(max_ticks):
        # Arrivals: Tasks with arrival == tick join the PENDING queue (FIFO).
        pending.extend(t for t in scenario.tasks if t.arrival == tick)

        # Placement: the strategy decides; the engine commits each placement
        # only if it still fits (ADR-0001 - the engine owns the invariant).
        for task, server in strategy.place(list(pending), scenario.servers):
            if server is None or task not in pending:
                continue
            if server.free_capacity >= task.demand:
                task.state = TaskState.RUNNING
                task.allocated_tick = tick
                server.used += task.demand
                pending.remove(task)
                running.append((task, server))

        # Metrics: snapshot what occupies each Server during this tick
        # (after placement, before completions release capacity).
        monitor.record_occupancy({s.name: s.used for s in scenario.servers})

        # Progress: includes Tasks placed this same tick, so a Task placed
        # at t with duration d runs from t to t+d-1 (ADR-0002).
        for task, server in list(running):
            task.remaining -= 1
            if task.remaining == 0:
                task.state = TaskState.DONE
                server.used -= task.demand
                running.remove((task, server))
                assert task.allocated_tick is not None
                monitor.record_completion(
                    wait=task.allocated_tick - task.arrival,
                    latency=server.latency_from(task.origin),
                    duration=task.duration,
                    tick=tick,
                    variety=server.variety,
                )

        if all(t.state is TaskState.DONE for t in scenario.tasks):
            return monitor

    unfinished = sum(1 for t in scenario.tasks if t.state is not TaskState.DONE)
    raise TickLimitExceededError(
        f"simulation hit the tick limit ({max_ticks}) with "
        f"{unfinished} task(s) not DONE; no metrics were reported"
    )
