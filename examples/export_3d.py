"""Bygger 3D-visaren för ett scenario som en fristående HTML-fil.

Användning:
    uv run python examples/export_3d.py scenarios/scenario3_mixed_robust.toml [dygn]

Sidan sparas som results/<namn>_3d.html och öppnas i webbläsaren. Den kan också
läggas på GitHub Pages, eftersom all banedata finns i filen.
"""

import sys
import time
import webbrowser
from pathlib import Path

from sepsim.export import export_trajectories
from sepsim.scenario import load_mission
from sepsim.viz.viewer import write_viewer

RESULTS = Path("results")


def main(scenario_path: str, days: float = 21.0) -> None:
    path = Path(scenario_path)
    mission = load_mission(path)
    RESULTS.mkdir(exist_ok=True)

    print(f"Propagating {days:g} days with J2 and drag…")
    start = time.time()
    data = export_trajectories(mission, days=days)
    print(f"Done in {time.time() - start:.0f} s. Closest passes:")
    for p in data["closest_passes"]:
        print(f"  {p['pair'][0]:>10} – {p['pair'][1]:<10} {p['distance_m']:8.1f} m at day {p['time_s'] / 86400:5.2f}")

    out = write_viewer(data, RESULTS / f"{path.stem}_3d.html")
    print(f"\nSaved {out} ({out.stat().st_size / 1e6:.1f} MB)")
    webbrowser.open(out.resolve().as_uri())


if __name__ == "__main__":
    main(sys.argv[1], float(sys.argv[2]) if len(sys.argv) > 2 else 21.0)