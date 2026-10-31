"""Optimerar separationsplanen för ett scenario och sparar den som en ny TOML-fil.

Användning:
    uv run python examples/optimize_scenario.py scenarios/scenario1.toml

Den optimerade planen sparas som scenarios/<namn>_optimized.toml och kan
sedan analyseras och ritas med run_scenario.py.
"""

import sys
import time
from pathlib import Path

import numpy as np

from sepsim.optimize import min_separation, optimize_plan
from sepsim.scenario import Mission, load_mission


def angles_from_direction(direction) -> tuple[float, float]:
    """Omvänd till direction_from_angles: enhetsvektor → (azimut, elevation) i grader."""
    x, y, z = np.asarray(direction, dtype=float) / np.linalg.norm(direction)
    azimuth = np.degrees(np.arctan2(x, y))
    elevation = np.degrees(np.arcsin(z))
    return azimuth, elevation


def save_mission(mission: Mission, path: Path, name: str) -> None:
    """Skriver ett uppdrag till en TOML-fil i samma format som load_mission läser."""
    lines = [
        f'name = "{name}"',
        f"altitude_km = {mission.altitude / 1000:g}",
        f"stage_mass_kg = {mission.stage_mass:g}",
    ]
    for sat in mission.satellites:
        az, el = angles_from_direction(sat.direction)
        d = ", ".join(f"{c:.6f}" for c in sat.direction)
        lines += [
            "",
            "[[satellites]]",
            f'name = "{sat.name}"',
            f"mass_kg = {sat.mass:g}",
            f"spring_impulse_Ns = {sat.spring_impulse:g}",
            f"direction = [{d}]     # azimuth {az:.1f}°, elevation {el:.1f}°",
            f"t_sep_s = {sat.t_sep:.1f}",
        ]
    path.write_text("\n".join(lines) + "\n")


def main(scenario_path: str) -> None:
    path = Path(scenario_path)
    mission = load_mission(path)

    naive = min_separation(mission)
    print(f"Original plan:  minimum distance {naive:8.1f} m")

    start = time.time()
    best_mission, best = optimize_plan(mission)
    print(
        f"Optimized plan: minimum distance {best:8.1f} m   ({time.time() - start:.0f} s)\n"
    )

    print(
        f"{'Satellite':<10} {'t_sep [s]':>10} {'azimuth':>9} {'elevation':>10} {'Δv [m/s]':>9}"
    )
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
