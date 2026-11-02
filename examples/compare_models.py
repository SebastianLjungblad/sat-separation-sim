"""Jämför CW med den numeriska modellen: när slutar CW stämma, och vilken kraft orsakar det?

Användning:
    uv run python examples/compare_models.py scenarios/scenario1_optimized.toml 3

Det andra argumentet är simuleringens längd i dygn (standard: 3).
"""

import sys
import time
from pathlib import Path

import numpy as np

from sepsim.analysis.conjunctions import closest_approach, pairwise_distances
from sepsim.constants import R_EARTH
from sepsim.dynamics.cw import mean_motion
from sepsim.dynamics.forces import ForceModel
from sepsim.dynamics.propagator import propagate_mission_numerical
from sepsim.dynamics.separation import propagate_mission, release_times
from sepsim.scenario import load_mission
from sepsim.viz.plots import plot_model_comparison

SAFETY = 10.0           # [m]
CLEARANCE = 600.0       # [s]
N_SAMPLES = 3000
RESULTS = Path("results")

MODELS = {
    "Two-body (round Earth)": ForceModel(j2=False, drag=False),
    "+ J2 only": ForceModel(j2=True, drag=False),
    "+ drag only": ForceModel(j2=False, drag=True),
    "J2 + drag": ForceModel(),
    "J2 + drag, high solar activity": ForceModel(solar_activity="high"),
}


def main(scenario_path: str, days: float) -> None:
    path = Path(scenario_path)
    mission = load_mission(path)
    n = mean_motion(R_EARTH + mission.altitude)
    t = np.linspace(0, days * 86400, N_SAMPLES)

    _, cw = propagate_mission(mission, n, t)
    pairs, d_cw = pairwise_distances(cw[:, :, :3])
    release = release_times(mission)
    after = [max(release[i], release[j]) + CLEARANCE for i, j in pairs]
    cw_min, _ = closest_approach(d_cw, t, after=after)

    print(f"{path.stem}, {days:g} days, inclination {mission.inclination_deg:g}°\n")
    print(f"{'Model':<34} {'CW error > 10 m after':>22} {'error at end':>13} {'min distance':>13}")
    print(f"{'CW (reference)':<34} {'':>22} {'':>13} {cw_min.min():11.0f} m")

    errors = {}
    for label, model in MODELS.items():
        start = time.time()
        _, numerical = propagate_mission_numerical(mission, t, model)
        _, d_num = pairwise_distances(numerical[:, :, :3])
        num_min, _ = closest_approach(d_num, t, after=after)

        err = np.abs(d_num - d_cw).max(axis=0)          # största felet över alla par, per tidpunkt
        errors[label] = err
        exceeded = np.nonzero(err > SAFETY)[0]
        when = f"{t[exceeded[0]] / 3600:8.1f} h" if len(exceeded) else "never"
        print(f"{label:<34} {when:>22} {err[-1]:11.0f} m {num_min.min():11.0f} m"
              f"   ({time.time() - start:.0f} s)")

    RESULTS.mkdir(exist_ok=True)
    fig = plot_model_comparison(t, errors, safety=SAFETY)
    out = RESULTS / f"{path.stem}_model_comparison.png"
    fig.savefig(out, dpi=150)
    print(f"\nFigure saved to {out}")


if __name__ == "__main__":
    if len(sys.argv) not in (2, 3):
        print("Usage: uv run python examples/compare_models.py <scenario.toml> [days]")
        sys.exit(1)
    main(sys.argv[1], float(sys.argv[2]) if len(sys.argv) == 3 else 3.0)