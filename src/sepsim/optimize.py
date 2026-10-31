from dataclasses import replace

import numpy as np

from sepsim.analysis.conjunctions import closest_approach, pairwise_distances
from sepsim.constants import R_EARTH
from sepsim.dynamics.cw import mean_motion
from sepsim.dynamics.separation import direction_from_angles, propagate_mission, release_times
from sepsim.scenario import Mission
from scipy.optimize import differential_evolution


def apply_plan(mission: Mission, params: np.ndarray) -> Mission:
    """
    Skapar ett nytt uppdrag med riktningar och separationstider från params:
    [az_1, el_1, ..., az_n, el_n, gap_2, ..., gap_n]

    Satelliterna släpps i den ordning de står i mission.satellites.
    Massor och fjädrar behålls.
    """
    n_sats = len(mission.satellites)
    angles = np.asarray(params[: 2 * n_sats]).reshape(n_sats, 2)   # en rad (az, el) per satellit
    gaps = np.asarray(params[2 * n_sats :])
    t_seps = np.concatenate([[0.0], np.cumsum(gaps)])              # [0, gap_2, gap_2 + gap_3]

    new_sats = [
        replace(sat, direction=tuple(direction_from_angles(az, el)), t_sep=float(t_sep))
        for sat, (az, el), t_sep in zip(mission.satellites, angles, t_seps)
    ]
    return replace(mission, satellites=new_sats)


def min_separation(mission: Mission, clearance: float = 600.0,
                   n_orbits: float = 1.5, n_samples: int = 2000) -> float:
    """
    Minsta avstånd [m] mellan något par av objekt efter frigångstiden.
    Simuleringen pågår n_orbits varv efter den sista separationen.
    """
    n = mean_motion(R_EARTH + mission.altitude)           # medelrörelsen för uppdragets banhöjd
    T = 2 * np.pi / n                                     # omloppstiden
    t_last = max(s.t_sep for s in mission.satellites)     # den senaste separationstiden bland satelliterna
    t = np.linspace(0, t_last + n_orbits * T, n_samples)

    # simulera, räkna avstånd, frigångstid per par, closest_approach
    # --- Simulering ---
    names, states = propagate_mission(mission, n, t)
    positions = states[:, :, :3]
    
        # --- Analys ---
    pairs, distances = pairwise_distances(positions)
    release = release_times(mission)
    after = [max(release[i], release[j]) + clearance for i, j in pairs]
    min_dist, _ = closest_approach(distances, t, after=after)

    return float(min_dist.min())    # det sämsta paret