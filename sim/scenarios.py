"""
Scenario factories: parameterized, reproducible infrastructure + load.

Responsibilities:
- Build the embedded Scenarios the CLI can run, from a seed and load
  parameters.
- Provide the low/high load presets and a randomized load factory whose
  output is fully determined by its seed (same seed -> same load).
"""

from dataclasses import dataclass, replace
from random import Random

from sim.model import Scenario, Server, ServerVariety, Task


@dataclass(frozen=True)
class LoadParams:
    """Parameters of a randomized load: how many Tasks and their ranges.

    Attributes:
        num_tasks: Number of Tasks to generate.
        arrival_window: Tasks arrive uniformly in ticks [0, arrival_window];
            a narrow window concentrates arrivals and drives contention.
        duration_min: Smallest Task duration in ticks (inclusive).
        duration_max: Largest Task duration in ticks (inclusive).
        demand_min: Smallest capacity demand of a Task (inclusive).
        demand_max: Largest capacity demand of a Task (inclusive).
    """

    num_tasks: int
    arrival_window: int
    duration_min: int
    duration_max: int
    demand_min: int
    demand_max: int


# Two contrasting loads over the same infrastructure: the low load is small
# and spread out (no contention), the high load is many, bursty, longer Tasks
# (contention shows up as waiting).
LOW_LOAD = LoadParams(
    num_tasks=6,
    arrival_window=15,
    duration_min=1,
    duration_max=2,
    demand_min=1,
    demand_max=1,
)
HIGH_LOAD = LoadParams(
    num_tasks=24,
    arrival_window=3,
    duration_min=3,
    duration_max=6,
    demand_min=1,
    demand_max=2,
)

LOAD_PRESETS: dict[str, LoadParams] = {"low": LOW_LOAD, "high": HIGH_LOAD}


def _edge_a_server() -> Server:
    """The Edge Server shared by every embedded Scenario topology.

    A fresh instance per call: Server.used is mutated in place by the
    engine, so sharing one instance across Scenarios would leak occupancy
    between runs.
    """
    return Server(name="edge-a", variety=ServerVariety.EDGE, capacity=2, site="edge-a")


def minimal_scenario(seed: int = 0) -> Scenario:
    """Builds the minimal embedded Scenario: one edge, one cloud, four Tasks.

    The load is a fixed list (no randomness yet), so `seed` does not change
    it; the parameter is part of the factory contract (CLI --seed) and will
    drive the randomized load of richer scenarios.

    Args:
        seed: Reproducibility seed; a fixed load ignores it.

    Returns:
        A small Scenario whose cloud (capacity 2) sees contention under
        AllCloud, so waits show up in the metrics.
    """
    return Scenario(
        servers=[
            _edge_a_server(),
            Server(name="cloud", variety=ServerVariety.CLOUD, capacity=2),
        ],
        tasks=[
            Task(arrival=0, origin="edge-a", duration=3),
            Task(arrival=0, origin="edge-a", duration=2),
            Task(arrival=1, origin="edge-a", duration=2),
            Task(arrival=2, origin="edge-a", duration=1),
        ],
    )


def _load_infrastructure() -> list[Server]:
    """The fixed infrastructure shared by the low and high load presets.

    Keeping the Servers identical across loads isolates the variable under
    study: only the load changes, so the ranking of strategies can be
    attributed to contention rather than to a different topology.
    """
    return [
        _edge_a_server(),
        Server(name="cloud", variety=ServerVariety.CLOUD, capacity=4),
    ]


def load_scenario(params: LoadParams, seed: int = 0) -> Scenario:
    """Builds a Scenario with a randomized load over the fixed infrastructure.

    All randomness is drawn from a single seeded generator, so the same
    seed and params always produce the same load (and thus the same
    metrics); different seeds produce different loads.

    Args:
        params: The load parameters (Task count and ranges).
        seed: Reproducibility seed for the random load.

    Returns:
        A Scenario whose Tasks are sorted by arrival tick.
    """
    rng = Random(seed)
    tasks = [
        Task(
            arrival=rng.randint(0, params.arrival_window),
            origin="edge-a",
            duration=rng.randint(params.duration_min, params.duration_max),
            demand=rng.randint(params.demand_min, params.demand_max),
        )
        for _ in range(params.num_tasks)
    ]
    tasks.sort(key=lambda task: task.arrival)
    return Scenario(servers=_load_infrastructure(), tasks=tasks)


def make_scenario(
    name: str, seed: int = 0, overrides: dict[str, int] | None = None
) -> Scenario:
    """Builds a Scenario by name, applying any load-parameter overrides.

    Args:
        name: Scenario to build ("minimal", or a load preset like "low"/"high").
        seed: Reproducibility seed forwarded to the factory.
        overrides: Load-parameter fields to override on the preset; ignored
            by the fixed "minimal" Scenario.

    Returns:
        The requested Scenario.

    Raises:
        KeyError: If name is not a known Scenario.
    """
    if name == "minimal":
        return minimal_scenario(seed=seed)
    params = replace(LOAD_PRESETS[name], **(overrides or {}))
    return load_scenario(params, seed=seed)


SCENARIO_NAMES: list[str] = ["minimal", *LOAD_PRESETS]
