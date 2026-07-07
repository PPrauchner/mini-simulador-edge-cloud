"""
CLI entry point: `python -m sim`.

Responsibilities:
- Parse the CLI flags (--scenario, --seed, --ticks, --strategy, --compare
  and the load overrides) with argparse, stdlib-only.
- Build the selected Scenario under the chosen strategy and print the metrics,
  or under --compare run every strategy on the same load and print the table.
"""

import argparse
import sys

from sim.engine import TickLimitExceededError, run
from sim.model import Scenario, ServerVariety
from sim.report import compare_table
from sim.scenarios import SCENARIO_NAMES, make_scenario
from sim.strategies import AllCloud, EdgeFirst, LeastLoaded, PlacementStrategy

# Maps the --strategy CLI value to its display name and Placement Strategy.
STRATEGIES: dict[str, tuple[str, type[PlacementStrategy]]] = {
    "allcloud": ("AllCloud", AllCloud),
    "edgefirst": ("EdgeFirst", EdgeFirst),
    "leastloaded": ("LeastLoaded", LeastLoaded),
}

# LoadParams fields overridable from the CLI; each flag (e.g. --num-tasks)
# lands on the identically named argparse attribute (args.num_tasks).
LOAD_OVERRIDE_FIELDS: tuple[str, ...] = (
    "num_tasks",
    "arrival_window",
    "duration_min",
    "duration_max",
    "demand_min",
    "demand_max",
)


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
        "--scenario",
        choices=SCENARIO_NAMES,
        default="minimal",
        help="scenario to run: fixed 'minimal' or a load preset (default: minimal)",
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
    parser.add_argument(
        "--compare",
        action="store_true",
        help="run every strategy on the same scenario and print a table",
    )
    load = parser.add_argument_group(
        "load parameters",
        "override the selected load preset (ignored by 'minimal')",
    )
    load.add_argument("--num-tasks", type=int, help="number of Tasks to generate")
    load.add_argument(
        "--arrival-window", type=int, help="Tasks arrive in ticks [0, window]"
    )
    load.add_argument("--duration-min", type=int, help="smallest Task duration (ticks)")
    load.add_argument("--duration-max", type=int, help="largest Task duration (ticks)")
    load.add_argument("--demand-min", type=int, help="smallest Task demand (units)")
    load.add_argument("--demand-max", type=int, help="largest Task demand (units)")
    args = parser.parse_args(argv)

    overrides = {
        field: getattr(args, field)
        for field in LOAD_OVERRIDE_FIELDS
        if getattr(args, field) is not None
    }

    def build_scenario() -> Scenario:
        # Rebuilt per strategy: run() mutates the Scenario in place, so each
        # strategy needs a fresh copy of the identical (same seed) load.
        return make_scenario(args.scenario, seed=args.seed, overrides=overrides)

    if args.compare:
        try:
            results = [
                (name, run(build_scenario(), strategy_cls(), max_ticks=args.ticks))
                for name, strategy_cls in STRATEGIES.values()
            ]
        except (TickLimitExceededError, ValueError) as error:
            print(f"error: {error}", file=sys.stderr)
            return 1
        print(f"scenario: {args.scenario}")
        print(compare_table(results))
        return 0

    display_name, strategy_cls = STRATEGIES[args.strategy]
    try:
        monitor = run(build_scenario(), strategy_cls(), max_ticks=args.ticks)
    except (TickLimitExceededError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    split = monitor.split
    print(f"scenario: {args.scenario} | strategy: {display_name}")
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
