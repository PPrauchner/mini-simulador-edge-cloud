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


class EdgeFirst(GreedyStrategy):
    """Prefers the local edge Server; falls back to the cloud.

    Places the Task on the edge Server at its origin site when that edge
    has slack; otherwise sends it to the cloud. Ties are broken by the
    Scenario's declared Server order (the first matching Server wins),
    which is stable and deterministic -- no randomness.
    """

    def place_one(self, task: Task, servers: list[Server]) -> Server | None:
        local_edge = next(
            (
                s
                for s in servers
                if s.variety is ServerVariety.EDGE
                and s.site == task.origin
                and s.free_capacity >= task.demand
            ),
            None,
        )
        if local_edge is not None:
            return local_edge
        return next(
            (s for s in servers if s.variety is ServerVariety.CLOUD), None
        )


class LeastLoaded(GreedyStrategy):
    """Places the Task on the Server with the most free capacity.

    Considers every Server -- the local edge, neighbor edges and the
    cloud alike. Ties are broken by the Scenario's declared Server order
    (the first Server reaching the maximum wins), which is stable and
    deterministic -- no randomness.
    """

    def place_one(self, task: Task, servers: list[Server]) -> Server | None:
        return max(servers, key=lambda s: s.free_capacity, default=None)
