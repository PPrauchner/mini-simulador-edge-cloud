"""
CLI entry point: `python -m sim`.

Responsibilities:
- Parse the CLI flags (--seed, --ticks, --strategy) with argparse, stdlib-only.
- Run the minimal embedded Scenario under the chosen strategy and print
  the metrics.
"""

import argparse
import sys

from sim.engine import TickLimitExceededError, run
from sim.model import ServerVariety
from sim.scenarios import minimal_scenario
from sim.strategies import AllCloud, EdgeFirst, LeastLoaded, PlacementStrategy

# Maps the --strategy CLI value to its display name and Placement Strategy.
STRATEGIES: dict[str, tuple[str, type[PlacementStrategy]]] = {
    "allcloud": ("AllCloud", AllCloud),
    "edgefirst": ("EdgeFirst", EdgeFirst),
    "leastloaded": ("LeastLoaded", LeastLoaded),
}


def main(argv: list[str] | None = None) -> int:
    """Runs the minimal Scenario under AllCloud and prints the metrics.

    Args:
        argv: CLI arguments; None means sys.argv[1:].

    Returns:
        Process exit code: 0 on success, 1 when the simulation fails.
    """
    parser = argparse.ArgumentParser(
        prog="sim",
        description=(
            "Discrete-time simulator for task placement across edge and "
            "cloud servers."
        ),
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="reproducibility seed for the scenario (default: 0)",
    )
    parser.add_argument(
        "--ticks",
        type=int,
        default=10_000,
        help="safety cap on simulated ticks (default: 10000)",
    )
    parser.add_argument(
        "--strategy",
        choices=sorted(STRATEGIES),
        default="allcloud",
        help="placement strategy to run (default: allcloud)",
    )
    args = parser.parse_args(argv)

    display_name, strategy_cls = STRATEGIES[args.strategy]
    scenario = minimal_scenario(seed=args.seed)
    try:
        monitor = run(scenario, strategy_cls(), max_ticks=args.ticks)
    except (TickLimitExceededError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    split = monitor.split
    print(f"scenario: minimal | strategy: {display_name}")
    print(f"mean response time: {monitor.mean_response_time:.2f} ticks")
    print(f"mean wait: {monitor.mean_wait:.2f} ticks")
    print(
        f"split edge/cloud: {split[ServerVariety.EDGE]} / "
        f"{split[ServerVariety.CLOUD]} tasks"
    )
    print("utilization per server:")
    for name, utilization in monitor.mean_utilization.items():
        print(f"  {name}: {utilization:.0%}")
    print(f"makespan: tick {monitor.makespan}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
