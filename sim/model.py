"""
Domain model of the edge-cloud simulator.

Responsibilities:
- Define the typed dataclasses for the domain vocabulary (see CONTEXT.md):
  Task, Server, Scenario and their supporting enums.
- Encode the latency-from-origin rule of each Server variety (ADR-0002:
  latency is accounting-only; it never delays execution).
"""

from dataclasses import dataclass, field
from enum import Enum

LOCAL_LATENCY = 1
NEIGHBOR_LATENCY = 3
CLOUD_LATENCY = 8


class ServerVariety(Enum):
    """The two varieties of Server: near, small Edge vs. far, large Cloud."""

    EDGE = "edge"
    CLOUD = "cloud"


class TaskState(Enum):
    """Lifecycle of a Task: PENDING -> RUNNING -> DONE."""

    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"


# eq=False: identity semantics — two Tasks (or Servers) with equal fields are
# still distinct individuals, so the engine's membership checks stay correct
# under homogeneous loads.
@dataclass(eq=False)
class Task:
    """A schedulable unit of work, born at an edge site.

    Attributes:
        arrival: Tick at which the Task enters the simulation.
        origin: Edge site where the Task is born; determines latency to
            each Server.
        duration: Ticks of execution the Task needs on a Server.
        demand: Capacity units the Task occupies while running.
        state: Current lifecycle state, managed by the engine.
        remaining: Execution ticks still to run, managed by the engine.
        allocated_tick: Tick of the placement, set by the engine.
    """

    arrival: int
    origin: str
    duration: int
    demand: int = 1
    state: TaskState = field(default=TaskState.PENDING, init=False)
    remaining: int = field(init=False)
    allocated_tick: int | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        self.remaining = self.duration


@dataclass(eq=False)
class Server:
    """An execution node that hosts Tasks up to its capacity.

    Attributes:
        name: Unique identifier of the Server.
        variety: Whether this Server is Edge or Cloud.
        capacity: Total capacity units available for concurrent Tasks.
        site: Edge site this Server lives at; None for Cloud servers.
        local_latency: Latency seen by Tasks born at this Server's site.
        neighbor_latency: Latency seen by Tasks born at another edge site.
        cloud_latency: Latency of this Server when it is Cloud variety.
        used: Capacity units currently occupied, managed by the engine.
    """

    name: str
    variety: ServerVariety
    capacity: int
    site: str | None = None
    local_latency: int = LOCAL_LATENCY
    neighbor_latency: int = NEIGHBOR_LATENCY
    cloud_latency: int = CLOUD_LATENCY
    used: int = field(default=0, init=False)

    @property
    def free_capacity(self) -> int:
        """Capacity units still available for new placements."""
        return self.capacity - self.used

    def latency_from(self, origin: str) -> int:
        """Latency to reach this Server from a Task's origin site.

        Args:
            origin: Edge site where the Task was born.

        Returns:
            The latency in Ticks: cloud latency for Cloud servers, local
            latency for the origin's own edge, neighbor latency otherwise.
        """
        if self.variety is ServerVariety.CLOUD:
            return self.cloud_latency
        return self.local_latency if origin == self.site else self.neighbor_latency


@dataclass
class Scenario:
    """A reproducible configuration of infrastructure + load.

    Attributes:
        servers: The infrastructure (Edge and Cloud Servers).
        tasks: The load, as a fixed list of Tasks with arrival ticks.
    """

    servers: list[Server]
    tasks: list[Task]
