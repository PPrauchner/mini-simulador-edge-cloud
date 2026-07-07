"""
Placement strategies: the pluggable policies that place Tasks on Servers.

Responsibilities:
- Define the batch-shaped PlacementStrategy interface (ADR-0001).
- Provide GreedyStrategy, the FIFO base that delegates to place_one.
- Provide the concrete strategies, starting with AllCloud.
"""

from abc import ABC, abstractmethod

from sim.model import Server, ServerVariety, Task


class PlacementStrategy(ABC):
    """Decides on which Server each PENDING Task is placed.

    Sees the current state (pending Tasks + Servers) and returns the
    placements; the engine validates feasibility (ADR-0001).
    """

    @abstractmethod
    def place(
        self, pending: list[Task], servers: list[Server]
    ) -> list[tuple[Task, Server | None]]:
        """Places the pending Tasks of a tick, in batch.

        Args:
            pending: Tasks waiting for a Server, in FIFO order.
            servers: Servers with their current free capacity and latency.

        Returns:
            One (task, server) pair per decision; None as server means
            the Task waits on purpose.
        """


class GreedyStrategy(PlacementStrategy):
    """Batch base that scans the FIFO queue delegating to place_one."""

    def place(
        self, pending: list[Task], servers: list[Server]
    ) -> list[tuple[Task, Server | None]]:
        return [(task, self.place_one(task, servers)) for task in pending]

    @abstractmethod
    def place_one(self, task: Task, servers: list[Server]) -> Server | None:
        """Chooses a Server for a single Task, or None to wait."""


class AllCloud(GreedyStrategy):
    """Baseline strategy: every Task goes to the cloud."""

    def place_one(self, task: Task, servers: list[Server]) -> Server | None:
        return next(
            (s for s in servers if s.variety is ServerVariety.CLOUD), None
        )
