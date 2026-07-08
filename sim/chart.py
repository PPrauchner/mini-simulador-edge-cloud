"""
Chart: renders the Monitor's collected series to an image with matplotlib.

Responsibilities:
- Plot Server occupancy over Ticks for a single run, and a per-strategy
  metric comparison for a --compare run, from the Monitor's data.
- Keep matplotlib an optional dependency: import it lazily, only when a
  chart is actually rendered, so the stdlib-only core never touches it.
"""

import os
from types import ModuleType

from sim.monitor import Monitor


class ChartDependencyError(RuntimeError):
    """Raised when a chart is requested but matplotlib is not installed."""


def _pyplot() -> ModuleType:
    """Imports pyplot with the headless Agg backend, or fails clearly.

    Returns:
        The matplotlib.pyplot module, configured to render to files.

    Raises:
        ChartDependencyError: If matplotlib is not installed.
    """
    try:
        import matplotlib
    except ImportError as error:
        raise ChartDependencyError(
            "matplotlib is required for --chart; install it with "
            "'pip install matplotlib'"
        ) from error
    matplotlib.use("Agg")  # File output only; no display needed.
    from matplotlib import pyplot as plt

    return plt


def render_occupancy(monitor: Monitor, path: str) -> None:
    """Plots each Server's occupancy over Ticks and saves it as a PNG.

    Args:
        monitor: Monitor of a single run; its per-Tick occupancy is the
            series drawn, one line per Server.
        path: Destination path for the PNG image.

    Raises:
        ChartDependencyError: If matplotlib is not installed.
    """
    plt = _pyplot()
    ticks = list(range(len(monitor.occupancy)))
    fig, ax = plt.subplots()
    for name in monitor.capacities:
        series = [snapshot.get(name, 0) for snapshot in monitor.occupancy]
        ax.plot(ticks, series, label=name)
    ax.set_xlabel("tick")
    ax.set_ylabel("occupied capacity (units)")
    ax.set_title("Server occupancy over time")
    ax.legend()
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    fig.savefig(path)
    plt.close(fig)


def render_comparison(results: list[tuple[str, Monitor]], path: str) -> None:
    """Plots response, wait and makespan per strategy as grouped bars.

    All three metrics share the Tick unit, so a single y-axis compares them
    honestly side by side.

    Args:
        results: Pairs of strategy display name and the Monitor of its run,
            in the order to display them (one group of bars each).
        path: Destination path for the PNG image.

    Raises:
        ChartDependencyError: If matplotlib is not installed.
    """
    plt = _pyplot()
    strategies = [name for name, _ in results]
    metrics = {
        "response": [monitor.mean_response_time for _, monitor in results],
        "wait": [monitor.mean_wait for _, monitor in results],
        "makespan": [monitor.makespan for _, monitor in results],
    }
    positions = range(len(strategies))
    width = 0.25
    fig, ax = plt.subplots()
    for offset, (label, values) in enumerate(metrics.items()):
        bars = [pos + (offset - 1) * width for pos in positions]
        ax.bar(bars, values, width, label=label)
    ax.set_xticks(list(positions))
    ax.set_xticklabels(strategies)
    ax.set_ylabel("ticks")
    ax.set_title("Strategy comparison")
    ax.legend()
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    fig.savefig(path)
    plt.close(fig)
