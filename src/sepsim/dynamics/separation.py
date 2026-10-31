import numpy as np

from sepsim.dynamics.cw import propagate_with_separation
from sepsim.scenario import Mission, Satellite


def separation_kicks(
    mission: Mission,
) -> list[tuple[Satellite, np.ndarray, np.ndarray]]:
    sats = sorted(mission.satellites, key=lambda s: s.t_sep)

    kicks = []
    for k, sat in enumerate(sats):
        m_rest = mission.stage_mass + sum(
            s.mass for s in sats[k + 1 :]
        )  # stegets massa + massan av satelliterna EFTER index k
        d = np.asarray(sat.direction, dtype=float)
        d_hat = d / np.linalg.norm(d)  # riktningen som enhetsvektor
        dv_sat = sat.spring_impulse / sat.mass * d_hat
        dv_stack = -sat.spring_impulse / m_rest * d_hat
        kicks.append((sat, dv_sat, dv_stack))

    return kicks


def propagate_mission(
    mission: Mission, n: float, t: np.ndarray
) -> tuple[list[str], np.ndarray]:
    """
    Propagerar raketsteget och alla satelliter relativt referensbanan,
    med rekyl på steget vid varje separation.

    Returnerar (namn, tillstånd) där tillstånd har formen
    (1 + antal_satelliter, N, 6). Objekt 0 är raketsteget.
    """
    kicks = separation_kicks(mission)

    # Rekylen från varje separation, propagerad från sin separationstid.
    recoils = [
        propagate_with_separation([0, 0, 0, *dv_stack], n, t, sat.t_sep)
        for sat, _, dv_stack in kicks
    ]

    stage = sum(recoils)  # 1. summan av alla rekyler

    names = ["Stage"]
    states = [stage]
    for k, (sat, dv_sat, _) in enumerate(kicks):
        own = propagate_with_separation(
            [0, 0, 0, *dv_sat], n, t, sat.t_sep
        )  # 2. satellitens egen knuff från sin t_sep
        inherited = sum(recoils[:k])  # 3. rekylerna från satelliterna före k
        names.append(sat.name)
        states.append(own + inherited)

    return names, np.stack(states)


def direction_from_angles(azimuth_deg: float, elevation_deg: float) -> np.ndarray:
    """
    Enhetsvektor i LVLH från azimut (i banplanet, 0° = framåt, 90° = utåt)
    och elevation (ut ur banplanet, 90° = tvärs banan).
    """

    az = np.radians(azimuth_deg)
    el = np.radians(elevation_deg)

    x = np.cos(el) * np.sin(az)
    y = np.cos(el) * np.cos(az)
    z = np.sin(el)

    return np.array([x, y, z])


def release_times(mission: Mission) -> np.ndarray:
    """Släpptid [s] per objekt i samma ordning som propagate_mission: steget först (0 s)."""
    sats = sorted(mission.satellites, key=lambda s: s.t_sep)
    return np.array([0.0] + [s.t_sep for s in sats])
