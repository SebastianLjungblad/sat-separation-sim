"""Omvandlingar mellan jordcentrerade koordinater (ECI) och LVLH."""

import numpy as np

from sepsim.constants import MU_EARTH


def circular_orbit_state(radius: float, inclination_deg: float) -> tuple[np.ndarray, np.ndarray]:
    """
    Position [m] och hastighet [m/s] i ECI för en cirkulär bana.
    Startpunkten ligger på ekvatorn, längs ECI:s x-axel.
    """
    i = np.radians(inclination_deg)                 # inklinationen i radianer
    v_circ = np.sqrt(MU_EARTH/radius)            # banhastigheten för en cirkulär bana: √(μ / radie)

    r = np.array([radius, 0.0, 0.0])                       # hela avståndet längs x
    v = v_circ * np.array([0.0, np.cos(i), np.sin(i)])     # farten gånger riktningen
    return r, v

def lvlh_basis(r: np.ndarray, v: np.ndarray) -> np.ndarray:
    """3×3-matris vars kolumner är LVLH-axlarna (utåt, framåt, åt sidan) i ECI."""
    x_hat = r / np.linalg.norm(r)          # utåt
    h = np.cross(r, v)                     # vinkelrät mot banplanet
    z_hat = h / np.linalg.norm(h)          # åt sidan
    y_hat = np.cross(z_hat, x_hat)         # framåt
    return np.column_stack([x_hat, y_hat, z_hat])

def _frame_rate(r_ref: np.ndarray, v_ref: np.ndarray) -> np.ndarray:
    """LVLH-ramens rotationshastighet [rad/s], uttryckt i LVLH: [0, 0, |r × v| / |r|²]."""
    return np.array([0.0, 0.0, np.linalg.norm(np.cross(r_ref, v_ref)) / np.dot(r_ref, r_ref)])


def lvlh_to_eci(r_ref: np.ndarray, v_ref: np.ndarray, rel_state: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Relativt tillstånd [x, y, z, vx, vy, vz] i LVLH → position och hastighet i ECI."""
    R = lvlh_basis(r_ref, v_ref)
    rho, rho_dot = np.asarray(rel_state[:3], float), np.asarray(rel_state[3:], float)
    omega = _frame_rate(r_ref, v_ref)

    r = r_ref + R @ rho
    v = v_ref + R @ (rho_dot + np.cross(omega, rho))
    return r, v


def eci_to_lvlh(r_ref: np.ndarray, v_ref: np.ndarray, r: np.ndarray, v: np.ndarray) -> np.ndarray:
    """Position och hastighet i ECI → relativt tillstånd [x, y, z, vx, vy, vz] i LVLH."""
    R = lvlh_basis(r_ref, v_ref)
    omega = _frame_rate(r_ref, v_ref)

    rho = R.T @ (r - r_ref)
    rho_dot = R.T @ (v - v_ref) - np.cross(omega, rho)
    return np.concatenate([rho, rho_dot])