"""
CLI entry point: `python -m sim`.

Responsibilities:
- Parse the CLI flags (--seed, --ticks) with argparse, stdlib-only.
- Run the minimal embedded Scenario under AllCloud and print the metrics.
"""

import argparse
import sys

from sim.engine import TickLimitExceededError, run
from sim.scenarios import minimal_scenario
from sim.strategies import AllCloud


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
    args = parser.parse_args(argv)

    scenario = minimal_scenario(seed=args.seed)
    try:
        monitor = run(scenario, AllCloud(), max_ticks=args.ticks)
    except (TickLimitExceededError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    print("scenario: minimal | strategy: AllCloud")
    print(f"mean response time: {monitor.mean_response_time:.2f} ticks")
    print(f"makespan: tick {monitor.makespan}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
