"""Tvåstegsoptimering: CW söker snabbt, den numeriska modellen väljer en plan som håller i en vecka.

Användning:
    uv run python examples/optimize_robust.py scenarios/scenario3_mixed.toml

1. CW-optimeraren tar fram de N bästa planerna för de första varven (~1 min).
2. Varje plan simuleras numeriskt (J2 + luftmotstånd) i 7 dygn, vid låg, medel
   och hög solaktivitet, parallellt på alla processorkärnor (några minuter).
3. Den plan vars sämsta fall är bäst väljs och sparas som <namn>_robust.toml.
"""

import sys
import time
from pathlib import Path

from sepsim.analysis.long_term import SOLAR_LEVELS, min_distance_over_time, rank_robust
from sepsim.dynamics.forces import ForceModel
from sepsim.optimize import optimize_candidates
from sepsim.scenario import load_mission, save_mission
from sepsim.viz.plots import plot_min_distance_over_time

N_CANDIDATES = 20
DAYS = 7.0
RESULTS = Path("results")


def main(scenario_path: str) -> None:
    path = Path(scenario_path)
    mission = load_mission(path)

    start = time.time()
    candidates = optimize_candidates(mission, n_candidates=N_CANDIDATES)
    print(f"Step 1: {len(candidates)} candidate plans from the CW optimizer ({time.time() - start:.0f} s)")

    start = time.time()
    rows = rank_robust(candidates, days=DAYS)
    print(f"Step 2: {len(candidates) * len(SOLAR_LEVELS)} numerical runs of {DAYS:g} days "
          f"({time.time() - start:.0f} s)\n")

    cw_favourite = max(rows, key=lambda r: r.cw_score)
    robust = rows[0]

    header = f"{'CW score':>9} " + " ".join(f"{lvl:>8}" for lvl in SOLAR_LEVELS) + f" {'worst':>8}  worst pair (medium)"
    print(header)
    for row in sorted(rows, key=lambda r: r.cw_score, reverse=True):
        mark = "  ← CW favourite" if row is cw_favourite else ("  ← robust choice" if row is robust else "")
        levels = " ".join(f"{row.results[lvl].min_distance:7.0f}m" for lvl in SOLAR_LEVELS)
        med = row.results["medium"]
        print(f"{row.cw_score:8.0f}m {levels} {row.worst_case:7.0f}m  {med.worst_pair} "
              f"at {med.time_days:.1f} d{mark}")

    out_cw = path.with_name(f"{path.stem}_optimized.toml")
    out_robust = path.with_name(f"{path.stem}_robust.toml")
    save_mission(cw_favourite.mission, out_cw, name=f"{path.stem} (CW favourite)")
    save_mission(robust.mission, out_robust, name=f"{path.stem} (robust)")
    print(f"\nSaved {out_cw} and {out_robust}")

    model = ForceModel(solar_activity="medium")
    t, d_cw = min_distance_over_time(cw_favourite.mission, DAYS, model)
    _, d_robust = min_distance_over_time(robust.mission, DAYS, model)
    RESULTS.mkdir(exist_ok=True)
    fig = plot_min_distance_over_time(
        t, {"CW favourite": d_cw, "Robust choice": d_robust},
        title="Closest distance between any pair (J2 + drag, medium solar activity)",
    )
    out = RESULTS / f"{path.stem}_robust_comparison.png"
    fig.savefig(out, dpi=150)
    print(f"Figure saved to {out}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: uv run python examples/optimize_robust.py <scenario.toml>")
        sys.exit(1)
    main(sys.argv[1])