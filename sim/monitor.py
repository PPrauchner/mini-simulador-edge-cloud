"""
Monitor: the observation structure that aggregates simulation metrics.

Responsibilities:
- Record what the engine reports (per-Tick occupancy and completions),
  without interfering with the simulation.
- Expose the aggregate metrics used to compare Placement Strategies.
"""

from dataclasses import dataclass, field
from statistics import fmean


@dataclass
class Completion:
    """The observed costs of one Task that reached DONE.

    Attributes:
        wait: Ticks spent PENDING (allocation tick - arrival).
        latency: Latency of the chosen Server, seen from the Task's origin.
        duration: Execution ticks of the Task.
        tick: Tick at which the Task reached DONE.
    """

    wait: int
    latency: int
    duration: int
    tick: int


@dataclass
class Monitor:
    """Collects per-Task completions and exposes aggregate metrics.

    Attributes:
        completions: One record per Task that reached DONE.
        occupancy: Per Tick (list index), the capacity units occupied on
            each Server, keyed by Server name.
    """

    completions: list[Completion] = field(default_factory=list)
    occupancy: list[dict[str, int]] = field(default_factory=list)

    def record_occupancy(self, occupancy: dict[str, int]) -> None:
        """Records the capacity units occupied on each Server this Tick.

        Args:
            occupancy: Occupied units keyed by Server name.
        """
        self.occupancy.append(occupancy)

    def record_completion(
        self, wait: int, latency: int, duration: int, tick: int
    ) -> None:
        """Records the observed costs of a Task that just reached DONE.

        Args:
            wait: Ticks the Task spent PENDING.
            latency: Latency of the chosen Server from the Task's origin.
            duration: Execution ticks of the Task.
            tick: Tick at which the Task reached DONE.
        """
        self.completions.append(Completion(wait, latency, duration, tick))

    @property
    def mean_response_time(self) -> float:
        """Mean of wait + latency + duration over all completed Tasks."""
        return fmean(c.wait + c.latency + c.duration for c in self.completions)

    @property
    def makespan(self) -> int:
        """Tick at which the last Task reached DONE (latency excluded)."""
        return max(c.tick for c in self.completions)
