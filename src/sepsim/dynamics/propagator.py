"""Numerisk propagering i ECI med valfria störningar (J2, luftmotstånd).

Varje objekt integreras för sig i ECI. Separationerna läggs in som momentana
hastighetsändringar, riktade i stackens LVLH-ram i separationsögonblicket.
Resultatet översätts till LVLH relativt en referenspunkt, så att det kan
analyseras och jämföras med CW på samma sätt som tidigare.
"""

import numpy as np
from scipy.integrate import solve_ivp

from sepsim.constants import R_EARTH
from sepsim.dynamics.forces import ForceModel, total_acceleration
from sepsim.dynamics.frames import circular_orbit_state, eci_to_lvlh, lvlh_basis
from sepsim.dynamics.separation import separation_kicks
from sepsim.scenario import Mission

RTOL = 1e-12    # relativ tolerans: hög, eftersom vi räknar meter på 6 878 000 m
ATOL = 1e-6     # absolut tolerans [m, m/s]


def integrate(state0: np.ndarray, t_start: float, t_eval: np.ndarray,
              cd_area_over_mass: float, model: ForceModel) -> np.ndarray:
    """
    Integrerar ett objekt i ECI från t_start.
    Returnerar tillstånd [x, y, z, vx, vy, vz] vid tiderna t_eval, form (len(t_eval), 6).
    """
    t_eval = np.asarray(t_eval, dtype=float)
    if len(t_eval) == 0:
        return np.zeros((0, 6))
    if t_eval[-1] <= t_start:                # ingen tid att integrera, t.ex. separation vid t = 0
        return np.tile(np.asarray(state0, dtype=float), (len(t_eval), 1))

    def derivatives(t, state):
        r, v = state[:3], state[3:]
        a = total_acceleration(r, v, cd_area_over_mass, model)
        return np.concatenate([v, a])        # d(position)/dt = v, d(hastighet)/dt = a

    sol = solve_ivp(derivatives, (t_start, t_eval[-1]), state0, t_eval=t_eval,
                    method="DOP853", rtol=RTOL, atol=ATOL)
    return sol.y.T


def propagate_mission_eci(mission: Mission, t: np.ndarray,
                          model: ForceModel = ForceModel()) -> tuple[list[str], np.ndarray, np.ndarray]:
    """
    Som propagate_mission_numerical, men returnerar tillstånden i ECI utan omvandling:
    (namn, tillstånd i ECI med form (antal_objekt, N, 6), referenspunktens tillstånd (N, 6)).
    Snabbare när bara avstånd behövs, eftersom avstånd är desamma i alla koordinatsystem.
    """
    """
    Propagerar raketsteget och alla satelliter numeriskt.

    Returnerar (namn, tillstånd i LVLH) med formen (1 + antal_satelliter, N, 6),
    samma format som propagate_mission, så att analyskoden kan återanvändas.
    LVLH-ramen följer en referenspunkt som propageras med samma gravitationsmodell
    men utan luftmotstånd.
    """
    t = np.asarray(t, dtype=float)
    r0, v0 = circular_orbit_state(R_EARTH + mission.altitude, mission.inclination_deg)
    start = np.concatenate([r0, v0])

    reference = integrate(start, 0.0, t, 0.0, ForceModel(j2=model.j2, drag=False))

    kicks = separation_kicks(mission)
    stage_cd_area = mission.stage_drag_coefficient * mission.stage_area

    stage_states = np.zeros((len(t), 6))
    stack = start
    t_now = 0.0
    attached_mass = sum(s.mass for s in mission.satellites)
    sat_states = []

    for sat, dv_sat, dv_stack in kicks:
        # 1. Stacken (steg + kvarvarande satelliter) fram till separationen
        segment = (t >= t_now) & (t < sat.t_sep)
        cd_am = stage_cd_area / (mission.stage_mass + attached_mass)
        out = integrate(stack, t_now, np.append(t[segment], sat.t_sep), cd_am, model)
        stage_states[segment] = out[:-1]
        stack = out[-1]

        # 2. Separationen: knuffarna riktas i stackens LVLH-ram just nu
        R = lvlh_basis(stack[:3], stack[3:])
        sat_start = stack.copy()
        sat_start[3:] += R @ dv_sat
        stack = stack.copy()
        stack[3:] += R @ dv_stack
        attached_mass -= sat.mass

        # 3. Satelliten på egen hand från separationen
        states = np.zeros((len(t), 6))
        released = t >= sat.t_sep
        cd_am_sat = sat.drag_coefficient * sat.area / sat.mass
        states[released] = integrate(sat_start, sat.t_sep, t[released], cd_am_sat, model)
        sat_states.append((sat.name, states, sat.t_sep))
        t_now = sat.t_sep

    # 4. Steget efter sista separationen
    segment = t >= t_now
    stage_states[segment] = integrate(stack, t_now, t[segment], stage_cd_area / mission.stage_mass, model)

    # Före sin separation sitter satelliten på stacken
    for _, states, t_sep in sat_states:
        attached = t < t_sep
        states[attached] = stage_states[attached]

    eci = np.stack([stage_states] + [states for _, states, _ in sat_states])
    names = ["Stage"] + [name for name, _, _ in sat_states]
    return names, eci, reference


def propagate_mission_numerical(mission: Mission, t: np.ndarray,
                                model: ForceModel = ForceModel()) -> tuple[list[str], np.ndarray]:
    """
    Propagerar raketsteget och alla satelliter numeriskt.

    Returnerar (namn, tillstånd i LVLH) med formen (1 + antal_satelliter, N, 6),
    samma format som propagate_mission, så att analyskoden kan återanvändas.
    LVLH-ramen följer en referenspunkt som propageras med samma gravitationsmodell
    men utan luftmotstånd.
    """
    t = np.asarray(t, dtype=float)
    names, eci, reference = propagate_mission_eci(mission, t, model)

    # Översätt till LVLH relativt referenspunkten
    lvlh = np.zeros_like(eci)
    for k in range(len(t)):
        r_ref, v_ref = reference[k, :3], reference[k, 3:]
        for obj in range(eci.shape[0]):
            lvlh[obj, k] = eci_to_lvlh(r_ref, v_ref, eci[obj, k, :3], eci[obj, k, 3:])

    return names, lvlh