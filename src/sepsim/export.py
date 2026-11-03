"""Export av ett uppdrag till 3D-visaren: banor i ECI, jordens rotation och solens riktning.

Visaren interpolerar mellan tidpunkterna med Hermite-interpolation (position och
hastighet i varje punkt). Med 60 s mellan punkterna blir felet i det relativa
avståndet mellan två objekt under en centimeter, se tests/test_export.py.
"""

import base64
from datetime import datetime, timedelta, timezone

import numpy as np

from sepsim.analysis.conjunctions import pairwise_distances
from sepsim.constants import OMEGA_EARTH, R_EARTH
from sepsim.dynamics.forces import ForceModel
from sepsim.dynamics.propagator import propagate_mission_eci
from sepsim.dynamics.separation import release_times
from sepsim.scenario import Mission

KICK_EPSILON = 1e-3     # [s] punkt strax före varje separation, så att ingen kurva interpoleras över en knuff


# --- Tid, jordens rotation och solen ---------------------------------------

def julian_date(when: datetime) -> float:
    """Juliansk dag (UTC används som UT1; skillnaden är under en sekund)."""
    j2000 = datetime(2000, 1, 1, 12, tzinfo=timezone.utc)
    return 2451545.0 + (when - j2000).total_seconds() / 86400.0


def gmst(when: datetime) -> float:
    """Greenwich Mean Sidereal Time [rad]: hur långt jorden har roterat relativt stjärnorna (IAU 1982)."""
    T = (julian_date(when) - 2451545.0) / 36525.0
    seconds = (67310.54841 + (876600 * 3600 + 8640184.812866) * T + 0.093104 * T**2 - 6.2e-6 * T**3)
    return np.radians((seconds % 86400.0) / 240.0)      # 240 s per grad


def sun_direction(when: datetime) -> np.ndarray:
    """Enhetsvektor mot solen i ECI (Astronomical Almanac, noggrann till ~0,01°)."""
    n = julian_date(when) - 2451545.0
    mean_longitude = np.radians((280.460 + 0.9856474 * n) % 360)
    mean_anomaly = np.radians((357.528 + 0.9856003 * n) % 360)
    ecliptic_longitude = (mean_longitude + np.radians(1.915) * np.sin(mean_anomaly)
                          + np.radians(0.020) * np.sin(2 * mean_anomaly))
    obliquity = np.radians(23.439 - 4e-7 * n)
    return np.array([np.cos(ecliptic_longitude),
                     np.cos(obliquity) * np.sin(ecliptic_longitude),
                     np.sin(obliquity) * np.sin(ecliptic_longitude)])


def raan_for_ltan(when: datetime, ltan_hours: float) -> float:
    """
    Banplanets vridning (RAAN) [rad] som ger en viss lokal soltid vid den uppstigande noden.
    Kl 12:00 ligger noden rakt under solen, varje timme vrider planet 15° österut.
    """
    sun = sun_direction(when)
    sun_right_ascension = np.arctan2(sun[1], sun[0])
    return sun_right_ascension + np.radians(15.0 * (ltan_hours - 12.0))


def rotate_z(vectors: np.ndarray, angle: float) -> np.ndarray:
    """Vrider vektorer (sista axeln: x, y, z eller x, y, z, vx, vy, vz) kring jordaxeln."""
    c, s = np.cos(angle), np.sin(angle)
    R = np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])
    out = np.array(vectors, dtype=float)
    out[..., 0:3] = out[..., 0:3] @ R.T
    if out.shape[-1] == 6:
        out[..., 3:6] = out[..., 3:6] @ R.T
    return out


# --- Tidpunkter och interpolation -----------------------------------------

def sample_times(mission: Mission, days: float, step: float) -> np.ndarray:
    """Jämnt utspridda tidpunkter, plus varje separation och en punkt strax före den."""
    t = np.arange(0.0, days * 86400.0 + step / 2, step)
    kicks = release_times(mission)[1:]                      # objekt 0 är steget
    extra = np.concatenate([kicks, kicks - KICK_EPSILON])
    return np.unique(np.concatenate([t, extra[extra > 0]]))


def hermite(t_query: np.ndarray, t: np.ndarray, states: np.ndarray) -> np.ndarray:
    """
    Kubisk Hermite-interpolation av positioner: använder position och hastighet i båda ändpunkter.
    states har formen (N, 6). Samma formel används i visaren (JavaScript).
    """
    k = np.clip(np.searchsorted(t, t_query, side="right") - 1, 0, len(t) - 2)
    h = t[k + 1] - t[k]
    s = ((t_query - t[k]) / h)[:, None]
    p0, v0, p1, v1 = states[k, :3], states[k, 3:], states[k + 1, :3], states[k + 1, 3:]
    h00 = 2 * s**3 - 3 * s**2 + 1
    h10 = s**3 - 2 * s**2 + s
    h01 = -2 * s**3 + 3 * s**2
    h11 = s**3 - s**2
    return h00 * p0 + h10 * h[:, None] * v0 + h01 * p1 + h11 * h[:, None] * v1


# --- Exporten -------------------------------------------------------------

def _base64(array: np.ndarray) -> str:
    """float64-data som base64-text: exakt och ungefär tre gånger mindre än JSON-tal."""
    return base64.b64encode(np.ascontiguousarray(array, dtype="<f8").tobytes()).decode("ascii")


def closest_passes(names: list[str], mission: Mission, t: np.ndarray, eci: np.ndarray,
                   clearance: float = 600.0) -> list[dict]:
    """Närmaste passagen för varje par efter frigångstiden, närmast först."""
    pairs, distances = pairwise_distances(eci[:, :, :3])
    release = release_times(mission)
    passes = []
    for (i, j), d in zip(pairs, distances):
        valid = t >= max(release[i], release[j]) + clearance
        k = np.flatnonzero(valid)[np.argmin(d[valid])]
        passes.append({"pair": [names[i], names[j]], "distance_m": float(d[k]), "time_s": float(t[k])})
    return sorted(passes, key=lambda p: p["distance_m"])


def export_trajectories(mission: Mission, days: float = 21.0, model: ForceModel = ForceModel(),
                        step: float = 60.0, epoch: datetime = datetime(2027, 3, 1, 10, 0, tzinfo=timezone.utc),
                        ltan_hours: float = 10.5, clearance: float = 600.0) -> dict:
    """
    Propagerar uppdraget numeriskt och packar allt visaren behöver i en dict (sparas som JSON).

    Fysiken är symmetrisk kring jordaxeln (tvåkropp, J2 och vår atmosfär beror bara på
    avståndet till jordaxeln och höjden), så banplanet kan vridas i efterhand till den
    RAAN som ger önskad lokal soltid – resultatet är exakt detsamma som att börja där.
    """
    t = sample_times(mission, days, step)
    names, eci, _ = propagate_mission_eci(mission, t, model)
    raan = raan_for_ltan(epoch, ltan_hours)
    eci = rotate_z(eci, raan)

    released_order = sorted(mission.satellites, key=lambda s: s.t_sep)    # samma ordning som names
    masses = [mission.stage_mass] + [s.mass for s in released_order]
    areas = [mission.stage_area] + [s.area for s in released_order]
    sun_t = np.arange(0.0, days * 86400.0 + 3600.0, 3600.0)            # solen rör sig ~1° per dygn
    sun = np.array([sun_direction(epoch + timedelta(seconds=float(s))) for s in sun_t])

    return {
        "format": "sepsim-trajectories/1",
        "epoch_utc": epoch.isoformat().replace("+00:00", "Z"),
        "earth": {"radius_m": R_EARTH, "omega_rad_s": OMEGA_EARTH, "gmst_at_epoch_rad": float(gmst(epoch))},
        "orbit": {"altitude_m": mission.altitude, "inclination_deg": mission.inclination_deg,
                  "raan_deg": float(np.degrees(raan) % 360), "ltan_hours": ltan_hours},
        "sun": {"t_s": _base64(sun_t), "direction": _base64(sun)},
        "t_s": _base64(t),
        "objects": [
            {"name": name, "mass_kg": float(mass), "area_m2": float(area), "release_s": float(release),
             "state": _base64(eci[k])}                                  # (N, 6): x, y, z, vx, vy, vz [m, m/s]
            for k, (name, mass, area, release) in enumerate(zip(names, masses, areas, release_times(mission)))
        ],
        "closest_passes": closest_passes(names, mission, t, eci, clearance),
        "model": {"j2": model.j2, "drag": model.drag, "solar_activity": model.solar_activity},
    }


def decode(array_b64: str, columns: int = 1) -> np.ndarray:
    """Omvändningen till _base64, för tester och felsökning."""
    data = np.frombuffer(base64.b64decode(array_b64), dtype="<f8")
    return data.reshape(-1, columns) if columns > 1 else data