"""Optimerar separationsplanen för ett scenario och sparar den som en ny TOML-fil.

Användning:
    uv run python examples/optimize_scenario.py scenarios/scenario1.toml

Den optimerade planen sparas som scenarios/<namn>_optimized.toml och kan
sedan analyseras och ritas med run_scenario.py.
"""

import sys
import time
from pathlib import Path

from sepsim.dynamics.separation import angles_from_direction
from sepsim.optimize import min_separation, optimize_plan
from sepsim.scenario import load_mission, save_mission


def main(scenario_path: str) -> None:
    path = Path(scenario_path)
    mission = load_mission(path)

    naive = min_separation(mission)
    print(f"Original plan:  minimum distance {naive:8.1f} m")

    start = time.time()
    best_mission, best = optimize_plan(mission)
    print(f"Optimized plan: minimum distance {best:8.1f} m   ({time.time() - start:.0f} s)\n")

    print(f"{'Satellite':<10} {'t_sep [s]':>10} {'azimuth':>9} {'elevation':>10} {'Δv [m/s]':>9}")
    for sat in best_mission.satellites:
        az, el = angles_from_direction(sat.direction)
        dv = sat.spring_impulse / sat.mass
        print(f"{sat.name:<10} {sat.t_sep:10.1f} {az:8.1f}° {el:9.1f}° {dv:9.2f}")

    out = path.with_name(f"{path.stem}_optimized.toml")
    save_mission(best_mission, out, name=f"{path.stem} (optimized)")
    print(f"\nSaved to {out}")
    print(f"Plot it with: uv run python examples/run_scenario.py {out}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: uv run python examples/optimize_scenario.py <scenario.toml>")
        sys.exit(1)
    main(sys.argv[1])