from dataclasses import replace

import numpy as np
from scipy.optimize import differential_evolution

from sepsim.analysis.mission import analyze_mission
from sepsim.dynamics.separation import (
    direction_from_angles,
)
from sepsim.scenario import Mission


def apply_plan(mission: Mission, params: np.ndarray) -> Mission:
    """
    Skapar ett nytt uppdrag med riktningar och separationstider från params:
    [az_1, el_1, ..., az_n, el_n, gap_2, ..., gap_n]

    Satelliterna släpps i den ordning de står i mission.satellites.
    Massor och fjädrar behålls.
    """
    n_sats = len(mission.satellites)
    angles = np.asarray(params[: 2 * n_sats]).reshape(
        n_sats, 2
    )  # en rad (az, el) per satellit
    gaps = np.asarray(params[2 * n_sats :])
    t_seps = np.concatenate([[0.0], np.cumsum(gaps)])  # [0, gap_2, gap_2 + gap_3]

    new_sats = [
        replace(sat, direction=tuple(direction_from_angles(az, el)), t_sep=float(t_sep))
        for sat, (az, el), t_sep in zip(mission.satellites, angles, t_seps)
    ]
    return replace(mission, satellites=new_sats)


def min_separation(
    mission: Mission,
    clearance: float = 600.0,
    n_orbits: float = 1.5,
    n_samples: int = 2000,
) -> float:
    """Minsta avstånd [m] mellan något par av objekt efter frigångstiden."""
    return float(
        analyze_mission(mission, clearance, n_orbits, n_samples).min_dist.min()
    )


def optimize_plan(
    mission: Mission,
    min_gap: float = 30.0,
    max_gap: float = 300.0,
    clearance: float = 600.0,
    maxiter: int = 150,
    popsize: int = 15,
    seed: int = 0,
) -> tuple[Mission, float]:
    """
    Söker den separationsplan (riktningar och mellanrum) som maximerar
    det minsta avståndet mellan alla par av objekt.

    Returnerar (bästa uppdrag, dess minsta avstånd [m]).
    """
    n_sats = len(mission.satellites)

    # Gränser: (az, el) per satellit, sedan ett mellanrum per separation efter den första
    bounds = [(-180.0, 180.0), (-90.0, 90.0)] * n_sats + [(min_gap, max_gap)] * (
        n_sats - 1
    )

    def objective(params: np.ndarray) -> float:
        # Optimeraren MINIMERAR, så vi ger den minus avståndet
        return -min_separation(apply_plan(mission, params), clearance=clearance)

    result = differential_evolution(
        objective,
        bounds,
        maxiter=maxiter,
        popsize=popsize,
        seed=seed,
        tol=1e-6,
        polish=False,
    )
    return apply_plan(mission, result.x), -result.fun
