"""Gemensam analys av ett uppdrag: simulering + minsta avstånd per par.

Används av både optimeraren (min_separation) och run_scenario.py, så att de
alltid bedömer en plan på exakt samma sätt.
"""

from dataclasses import dataclass

import numpy as np

from sepsim.analysis.conjunctions import closest_approach, pairwise_distances
from sepsim.constants import R_EARTH
from sepsim.dynamics.cw import mean_motion
from sepsim.dynamics.separation import propagate_mission, release_times
from sepsim.scenario import Mission


@dataclass
class MissionAnalysis:
    names: list[str]  # objektens namn, steget först
    t: np.ndarray  # [s] tidpunkter, form (N,)
    states: np.ndarray  # [m, m/s] tillstånd, form (antal_objekt, N, 6)
    pairs: list[tuple[int, int]]  # alla par (i, j)
    distances: np.ndarray  # [m] avstånd per par och tidpunkt, form (antal_par, N)
    min_dist: np.ndarray  # [m] minsta avstånd per par efter frigångstiden
    t_min: np.ndarray  # [s] när det minsta avståndet inträffar, per par
    period: float  # [s] omloppstid

    @property
    def positions(self) -> np.ndarray:
        """Bara positionerna, form (antal_objekt, N, 3)."""
        return self.states[:, :, :3]


def analyze_mission(
    mission: Mission,
    clearance: float = 600.0,
    n_orbits: float = 1.5,
    n_samples: int = 5000,
) -> MissionAnalysis:
    """
    Simulerar uppdraget i n_orbits varv efter den sista separationen och räknar
    ut minsta avstånd per par, med frigångstid räknad från den senare
    separationen i varje par.
    """
    n = mean_motion(R_EARTH + mission.altitude)
    T = 2 * np.pi / n
    t_last = max(s.t_sep for s in mission.satellites)
    t = np.linspace(0, t_last + n_orbits * T, n_samples)

    names, states = propagate_mission(mission, n, t)
    pairs, distances = pairwise_distances(states[:, :, :3])
    release = release_times(mission)
    after = [max(release[i], release[j]) + clearance for i, j in pairs]
    min_dist, t_min = closest_approach(distances, t, after=after)

    return MissionAnalysis(names, t, states, pairs, distances, min_dist, t_min, T)
