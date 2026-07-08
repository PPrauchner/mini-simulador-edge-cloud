"""
Report: assembles the console comparison table from collected metrics.

Responsibilities:
- Turn each strategy's Monitor into one row of the comparison table (one
  column per canonical metric), so strategies can be compared side by side.
- Keep table presentation out of the Monitor, which only collects.
"""

from sim.model import ServerVariety
from sim.monitor import Monitor


def compare_table(results: list[tuple[str, Monitor]]) -> str:
    """Assembles the comparison table: one row per strategy, one per metric.

    All strategies must have run over the same Scenario, so every Monitor
    shares the same Servers; their names become the utilization columns.

    Args:
        results: Pairs of strategy display name and the Monitor of its run,
            in the order to display them (one row each).

    Returns:
        The rendered table as a single multi-line string, header first.

    Raises:
        ValueError: If results is empty, or if the Monitors did not run
            over the same Scenario (their Servers differ).
    """
    if not results:
        raise ValueError("compare_table requires at least one result")
    server_names = list(results[0][1].capacities)
    for name, monitor in results:
        if list(monitor.capacities) != server_names:
            raise ValueError(
                f"{name}'s Monitor ran over different Servers than "
                f"{results[0][0]}'s; compare_table requires every "
                "strategy to run over the same Scenario"
            )

    headers = ["strategy", "response", "wait", "edge/cloud"]
    headers += [f"util:{name}" for name in server_names]
    headers += ["makespan"]

    rows = [headers]
    for name, monitor in results:
        split = monitor.split
        utilization = monitor.mean_utilization
        row = [
            name,
            f"{monitor.mean_response_time:.2f}",
            f"{monitor.mean_wait:.2f}",
            f"{split[ServerVariety.EDGE]}/{split[ServerVariety.CLOUD]}",
        ]
        row += [f"{utilization[server]:.0%}" for server in server_names]
        row.append(str(monitor.makespan))
        rows.append(row)

    widths = [max(len(row[col]) for row in rows) for col in range(len(headers))]
    lines = [
        "  ".join(
            [row[0].ljust(widths[0])]
            + [row[col].rjust(widths[col]) for col in range(1, len(headers))]
        )
        for row in rows
    ]
    return "\n".join(lines)
