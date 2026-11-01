"""Accelerationer i ECI: gravitation (rund jord), J2 och luftmotstånd."""

from dataclasses import dataclass

import numpy as np

from sepsim.constants import J2, MU_EARTH, OMEGA_EARTH, R_EARTH

# Exponentiell atmosfär kring 500 km (Vallado, Fundamentals of Astrodynamics)
RHO_500KM = 6.967e-13       # [kg/m³] täthet vid 500 km, medelförhållanden
SCALE_HEIGHT = 63.822e3     # [m] tätheten minskar med faktorn e per 63,8 km

# Ungefärlig skalning med solaktivitet
SOLAR_ACTIVITY_FACTOR = {"low": 0.3, "medium": 1.0, "high": 3.0}


def accel_two_body(r: np.ndarray) -> np.ndarray:
    """Gravitation från en rund jord: −μ r / |r|³."""
    return -MU_EARTH * r / np.linalg.norm(r)**3


def accel_j2(r: np.ndarray) -> np.ndarray:
    """Extra gravitation från jordens tillplattning (J2)."""
    x, y, z = r
    r_norm = np.linalg.norm(r)
    k = -1.5 * J2 * MU_EARTH * R_EARTH**2 / r_norm**5
    zz = 5.0 * z**2 / r_norm**2
    return k * np.array([x * (1.0 - zz), y * (1.0 - zz), z * (3.0 - zz)])


def atmospheric_density(altitude: float, solar_activity: str = "medium") -> float:
    """Luftens täthet [kg/m³] med en exponentiell modell kring 500 km."""
    return SOLAR_ACTIVITY_FACTOR[solar_activity] * RHO_500KM * np.exp(-(altitude - 500e3) / SCALE_HEIGHT)


def accel_drag(r: np.ndarray, v: np.ndarray, cd_area_over_mass: float,
               solar_activity: str = "medium") -> np.ndarray:
    """Luftmotstånd: −½ ρ (Cd A / m) |v_rel| v_rel. Atmosfären roterar med jorden."""
    altitude = np.linalg.norm(r) - R_EARTH
    rho = atmospheric_density(altitude, solar_activity)
    v_rel = v - np.cross([0.0, 0.0, OMEGA_EARTH], r)
    return -0.5 * rho * cd_area_over_mass * np.linalg.norm(v_rel) * v_rel


@dataclass
class ForceModel:
    """Vilka krafter som är påslagna."""
    j2: bool = True
    drag: bool = True
    solar_activity: str = "medium"


def total_acceleration(r: np.ndarray, v: np.ndarray, cd_area_over_mass: float,
                       model: ForceModel) -> np.ndarray:
    """Summan av alla påslagna accelerationer [m/s²] i ECI."""
    a = accel_two_body(r)
    if model.j2:
        a = a + accel_j2(r)
    if model.drag:
        a = a + accel_drag(r, v, cd_area_over_mass, model.solar_activity)
    return a