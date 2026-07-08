"""
Scenario factories: parameterized, reproducible infrastructure + load.

Responsibilities:
- Build the embedded Scenarios the CLI can run, from a seed and load
  parameters.
"""

from sim.model import Scenario, Server, ServerVariety, Task


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
            Server(name="edge-a", variety=ServerVariety.EDGE, capacity=2, site="edge-a"),
            Server(name="cloud", variety=ServerVariety.CLOUD, capacity=2),
        ],
        tasks=[
            Task(arrival=0, origin="edge-a", duration=3),
            Task(arrival=0, origin="edge-a", duration=2),
            Task(arrival=1, origin="edge-a", duration=2),
            Task(arrival=2, origin="edge-a", duration=1),
        ],
    )
