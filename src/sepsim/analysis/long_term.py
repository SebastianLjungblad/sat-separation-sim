"""Långtidsanalys med den numeriska modellen: minsta avstånd under flera dygn."""

from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass

import numpy as np

from sepsim.analysis.conjunctions import closest_approach, pairwise_distances
from sepsim.dynamics.forces import ForceModel
from sepsim.dynamics.propagator import propagate_mission_eci
from sepsim.dynamics.separation import release_times
from sepsim.scenario import Mission


@dataclass
class LongTermResult:
    min_distance: float     # [m] minsta avstånd mellan något par under hela perioden
    worst_pair: str         # vilket par, t.ex. "Stage–PanelSat"
    time_days: float        # [dygn] när det inträffade


def long_term_min_separation(mission: Mission, days: float = 7.0, model: ForceModel = ForceModel(),
                             clearance: float = 600.0, n_samples: int = 12000) -> LongTermResult:
    """Simulerar uppdraget numeriskt i `days` dygn och hittar den närmaste passagen."""
    t = np.linspace(0, days * 86400, n_samples)
    names, eci, _ = propagate_mission_eci(mission, t, model)

    # Avstånd är desamma i alla koordinatsystem, så de räknas direkt i ECI
    pairs, distances = pairwise_distances(eci[:, :, :3])
    release = release_times(mission)
    after = [max(release[i], release[j]) + clearance for i, j in pairs]
    min_dist, t_min = closest_approach(distances, t, after=after)

    k = int(np.argmin(min_dist))
    i, j = pairs[k]
    return LongTermResult(float(min_dist[k]), f"{names[i]}–{names[j]}", float(t_min[k] / 86400))


def evaluate_many(missions: list[Mission], days: float = 7.0, model: ForceModel = ForceModel(),
                  workers: int | None = None) -> list[LongTermResult]:
    """Kör long_term_min_separation för många planer parallellt, en per processorkärna."""
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(long_term_min_separation, m, days, model) for m in missions]
        return [f.result() for f in futures]


SOLAR_LEVELS = ("low", "medium", "high")


@dataclass
class RobustRow:
    mission: Mission
    cw_score: float                             # [m] CW-optimerarens betyg (första varven)
    results: dict[str, LongTermResult]          # långtidsresultat per solaktivitet

    @property
    def worst_case(self) -> float:
        """Sämsta minsta avstånd över alla solaktiviteter och CW-betyget."""
        return min(self.cw_score, *(r.min_distance for r in self.results.values()))


def rank_robust(candidates: list[tuple[Mission, float]], days: float = 7.0,
                levels: tuple[str, ...] = SOLAR_LEVELS, workers: int | None = None) -> list[RobustRow]:
    """
    Prövar varje kandidatplan med den numeriska modellen vid varje solaktivitet,
    och sorterar dem efter sämsta fall (störst först).
    Luftens täthet är den mest osäkra parametern, så planen ska klara alla nivåer.
    """
    missions = [m for m, _ in candidates]
    jobs = [(m, level) for m in missions for level in levels]
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(long_term_min_separation, m, days, ForceModel(solar_activity=level))
                   for m, level in jobs]
        results = [f.result() for f in futures]

    rows = []
    for c, (mission, cw_score) in enumerate(candidates):
        per_level = {level: results[c * len(levels) + k] for k, level in enumerate(levels)}
        rows.append(RobustRow(mission, cw_score, per_level))
    return sorted(rows, key=lambda row: row.worst_case, reverse=True)


def min_distance_over_time(mission: Mission, days: float = 7.0, model: ForceModel = ForceModel(),
                           clearance: float = 600.0, n_samples: int = 12000) -> tuple[np.ndarray, np.ndarray]:
    """Kortaste avståndet mellan något par vid varje tidpunkt (efter varje pars frigångstid)."""
    t = np.linspace(0, days * 86400, n_samples)
    _, eci, _ = propagate_mission_eci(mission, t, model)
    pairs, distances = pairwise_distances(eci[:, :, :3])
    release = release_times(mission)
    after = np.array([max(release[i], release[j]) + clearance for i, j in pairs])
    valid = t[np.newaxis, :] >= after[:, np.newaxis]
    return t, np.where(valid, distances, np.inf).min(axis=0)