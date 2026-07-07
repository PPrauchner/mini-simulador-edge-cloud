"""
Tests for placement strategies via the public `strategy.place(...)` seam.

Responsibilities:
- Verify each strategy's placement decision over a hand-built state
  (pending Tasks + Servers), per ADR-0001.
"""

from sim.model import Server, ServerVariety, Task
from sim.strategies import AllCloud, EdgeFirst, LeastLoaded


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


def test_edge_first_chooses_local_edge_when_it_has_slack() -> None:
    servers = make_servers()
    task = Task(arrival=0, origin="edge-a", duration=2)

    [(_, server)] = EdgeFirst().place([task], servers)

    assert server is not None
    assert server.name == "edge-a"


def test_edge_first_falls_back_to_cloud_when_local_edge_is_full() -> None:
    servers = make_servers()
    edge = next(s for s in servers if s.name == "edge-a")
    edge.used = edge.capacity  # no slack left on the local edge
    task = Task(arrival=0, origin="edge-a", duration=2)

    [(_, server)] = EdgeFirst().place([task], servers)

    assert server is not None
    assert server.variety is ServerVariety.CLOUD


def test_least_loaded_chooses_server_with_most_free_capacity() -> None:
    servers = make_servers()  # edge-a: cap 2, cloud: cap 10
    task = Task(arrival=0, origin="edge-a", duration=1)

    [(_, server)] = LeastLoaded().place([task], servers)

    assert server is not None
    assert server.name == "cloud"


def test_least_loaded_breaks_ties_by_declared_server_order() -> None:
    # Two Servers with identical free capacity: the first declared wins.
    servers = [
        Server(name="edge-a", variety=ServerVariety.EDGE, capacity=5, site="edge-a"),
        Server(name="edge-b", variety=ServerVariety.EDGE, capacity=5, site="edge-b"),
    ]
    task = Task(arrival=0, origin="edge-a", duration=1)

    [(_, server)] = LeastLoaded().place([task], servers)

    assert server is not None
    assert server.name == "edge-a"
