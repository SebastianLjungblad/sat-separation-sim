"""Clohessy–Wiltshire: analytisk relativ rörelse kring en cirkulär referensbana.

Koordinatsystem LVLH (följer med referenspunkten, dvs. dispensern):
    x: radiellt utåt från jorden
    y: längs banan (i färdriktningen)
    z: tvärs banan (längs banans normal)

Giltighet: cirkulär referensbana, små avstånd jämfört med banradien,
inga störningar (J2, luftmotstånd m.m.).
"""

import numpy as np

from sepsim.constants import MU_EARTH


def mean_motion(a: float) -> float:
    """Medelrörelse n [rad/s] för en cirkulär bana med radie a [m]."""
    return np.sqrt(MU_EARTH / a**3)


def cw_propagate(state0: np.ndarray, n: float, t: np.ndarray) -> np.ndarray:
    """
    Propagerar ett relativt tillstånd med Clohessy–Wiltshire.

    state0: [x, y, z, vx, vy, vz] i LVLH [m, m/s], form (6,)
    n:      medelrörelse [rad/s]
    t:      tidpunkter [s] efter separation, form (N,)
    Returnerar: tillstånd vid varje tidpunkt, form (N, 6)
    """
    x0, y0, z0, vx0, vy0, vz0 = np.asarray(state0, dtype=float)
    t = np.atleast_1d(np.asarray(t, dtype=float))

    nt = n * t
    c = np.cos(nt)
    s = np.sin(nt)

    # Positioner
    x = (4 - 3 * c) * x0 + (s / n) * vx0 + (2 / n) * (1 - c) * vy0
    y = (
        6 * (s - nt) * x0
        + y0
        + (2 / n) * (c - 1) * vx0
        + (1 / n) * (4 * s - 3 * nt) * vy0
    )
    z = c * z0 + (s / n) * vz0

    # Hastigheter (tidsderivator av positionerna ovan)
    vx = 3 * n * s * x0 + c * vx0 + 2 * s * vy0
    vy = 6 * n * (c - 1) * x0 - 2 * s * vx0 + (4 * c - 3) * vy0
    vz = -n * s * z0 + c * vz0

    return np.column_stack([x, y, z, vx, vy, vz])


def propagate_with_separation(
    state0: np.ndarray, n: float, t: np.ndarray, t_sep: float
) -> np.ndarray:
    """
    Propagerar en satellit som separeras från dispensern vid t_sep.

    Före t_sep: satelliten sitter på dispensern (tillstånd = 0).
    Efter t_sep: CW-rörelse med tiden räknad från separationen.

    state0: tillstånd precis efter separation [x, y, z, vx, vy, vz], form (6,)
    n:      medelrörelse [rad/s]
    t:      tidpunkter [s] från uppdragets start, form (N,)
    t_sep:  separationstidpunkt [s]
    Returnerar: form (N, 6)
    """
    t = np.atleast_1d(np.asarray(t, dtype=float))
    states = np.zeros((len(t), 6))

    released = t >= t_sep
    states[released] = cw_propagate(state0, n, t[released] - t_sep)

    return states


def separation_state(direction, speed: float = 1.0) -> np.ndarray:
    """
    Starttillstånd precis efter separation: position i dispensern,
    hastighet med given fart [m/s] i given riktning (behöver inte vara normerad).

    direction: [dx, dy, dz] i LVLH
    """
    d = np.asarray(direction, dtype=float)
    v = speed * d / np.linalg.norm(d)
    return np.array([0.0, 0.0, 0.0, *v])
