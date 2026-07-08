"""
Tests for placement strategies via the public `strategy.place(...)` seam.

Responsibilities:
- Verify each strategy's placement decision over a hand-built state
  (pending Tasks + Servers), per ADR-0001.
"""

from sim.model import Server, ServerVariety, Task
from sim.strategies import AllCloud


def make_servers() -> list[Server]:
    """Builds one edge and one cloud Server for strategy tests."""
    return [
        Server(name="edge-a", variety=ServerVariety.EDGE, capacity=2, site="edge-a"),
        Server(name="cloud", variety=ServerVariety.CLOUD, capacity=10),
    ]


def test_all_cloud_always_places_on_cloud() -> None:
    servers = make_servers()
    pending = [
        Task(arrival=0, origin="edge-a", duration=2),
        Task(arrival=0, origin="edge-a", duration=3),
    ]

    placements = AllCloud().place(pending, servers)

    assert len(placements) == len(pending)
    for task, server in placements:
        assert server is not None
        assert server.variety is ServerVariety.CLOUD


def test_all_cloud_keeps_fifo_order() -> None:
    servers = make_servers()
    first = Task(arrival=0, origin="edge-a", duration=1)
    second = Task(arrival=1, origin="edge-a", duration=1)

    placements = AllCloud().place([first, second], servers)

    assert [task for task, _ in placements] == [first, second]
