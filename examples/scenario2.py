"""Scenario 2: separationer med komponent längs banan → satelliterna driver isär."""

from pathlib import Path

import numpy as np

from sepsim.analysis.conjunctions import closest_approach, pairwise_distances
from sepsim.constants import R_EARTH
from sepsim.dynamics.cw import mean_motion, propagate_with_separation, separation_state
from sepsim.viz.plots import plot_distances, plot_trajectories

# --- Inställningar ---
ALTITUDE = 500e3        # [m] banhöjd
SAFETY = 10.0           # [m] säkerhetsavstånd
CLEARANCE = 600.0       # [s] frigångstid som ignoreras i analysen

RESULTS = Path("results")
RESULTS.mkdir(exist_ok=True)

N = mean_motion(R_EARTH + ALTITUDE)
T = 2 * np.pi / N
t = np.linspace(0, 1.5 * T, 5000)

# --- Scenariot: (namn, separationstid [s], starttillstånd [x, y, z, vx, vy, vz]) ---
# Skillnad mot scenario 1: varje satellit har en hastighet längs banan (vy),
# och olika stor, så att de driver isär i olika takt och aldrig kommer tillbaka.
satellites = [
    ("Sat 1", 0.0,   separation_state([ 0.3,  1.0, 0.0])),   # mest framåt
    ("Sat 2", 60.0,  separation_state([-0.3, -1.0, 0.0])),   # mest bakåt
    ("Sat 3", 120.0, separation_state([ 0.6,  0.5, 0.6])),   # snett framåt, uppåt och åt sidan
]

# --- Simulering ---
labels = ["Dispenser"] + [name for name, _, _ in satellites]

dispenser = np.zeros((len(t), 3))
sat_positions = [
    propagate_with_separation(state0, N, t, t_sep)[:, :3]
    for _, t_sep, state0 in satellites
]
positions = np.stack([dispenser, *sat_positions])

# --- Analys ---
pairs, distances = pairwise_distances(positions)
min_dist, t_min = closest_approach(distances, t, after=CLEARANCE)

print(f"Orbital period: {T / 60:.1f} min\n")
for (i, j), d, tm in zip(pairs, min_dist, t_min):
    status = "RISK" if d < SAFETY else "ok"
    print(f"{labels[i]:>9} – {labels[j]:<9}  min {d:9.1f} m at {tm / 60:6.1f} min  [{status}]")

# --- Grafer ---
fig = plot_distances(pairs, distances, t, labels, safety=SAFETY)
fig.savefig(RESULTS / "scenario2_distances.png", dpi=150)

fig = plot_trajectories(positions, labels)
fig.savefig(RESULTS / "scenario2_trajectories.png", dpi=150)

print("\nFigures saved to results/")