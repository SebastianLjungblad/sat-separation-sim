"""Kör ett scenario från en TOML-fil: simulering, avståndsanalys och grafer.

Användning:
    uv run python examples/run_scenario.py scenarios/scenario1.toml
"""

import sys
import tomllib
from pathlib import Path

import numpy as np

from sepsim.analysis.mission import analyze_mission
from sepsim.scenario import load_mission
from sepsim.viz.plots import plot_distances, plot_trajectories

SAFETY = 10.0  # [m] säkerhetsavstånd
CLEARANCE = 600.0  # [s] frigångstid efter varje separation
N_ORBITS = 1.5  # antal varv att simulera efter sista separationen

RESULTS = Path("results")


def main(scenario_path: str) -> None:
    path = Path(scenario_path)
    mission = load_mission(path)
    with open(path, "rb") as f:
        title = tomllib.load(f).get("name", path.stem)

    result = analyze_mission(mission, clearance=CLEARANCE, n_orbits=N_ORBITS)
    names = result.names

    print(title)
    print(f"Orbital period: {result.period / 60:.1f} min\n")
    for (i, j), d, tm in zip(result.pairs, result.min_dist, result.t_min):
        status = "RISK" if d < SAFETY else "ok"
        print(
            f"{names[i]:>6} – {names[j]:<6}  min {d:9.1f} m at {tm / 60:6.1f} min  [{status}]"
        )

    stage_end = result.positions[0, -1]
    print(
        f"\nStage displacement from reference point at end of simulation: "
        f"{np.linalg.norm(stage_end):.0f} m  (x={stage_end[0]:.0f}, y={stage_end[1]:.0f}, z={stage_end[2]:.0f})"
    )

    RESULTS.mkdir(exist_ok=True)
    stem = path.stem
    fig = plot_distances(result.pairs, result.distances, result.t, names, safety=SAFETY)
    fig.savefig(RESULTS / f"{stem}_distances.png", dpi=150)
    fig = plot_trajectories(result.positions, names)
    fig.savefig(RESULTS / f"{stem}_trajectories.png", dpi=150)
    print(f"\nFigures saved to {RESULTS}/{stem}_*.png")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: uv run python examples/run_scenario.py <scenario.toml>")
        sys.exit(1)
    main(sys.argv[1])
