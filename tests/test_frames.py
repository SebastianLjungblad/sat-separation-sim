import numpy as np
import pytest

from sepsim.constants import MU_EARTH, R_EARTH
from sepsim.dynamics.cw import mean_motion
from sepsim.dynamics.frames import circular_orbit_state, eci_to_lvlh, lvlh_basis, lvlh_to_eci

A = R_EARTH + 500e3


@pytest.mark.parametrize("inclination", [0.0, 51.6, 90.0, 97.4])
def test_circular_orbit_state(inclination):
    r, v = circular_orbit_state(A, inclination)
    assert np.allclose(r, [A, 0, 0])
    assert np.linalg.norm(v) == pytest.approx(np.sqrt(MU_EARTH / A))   # rätt fart
    assert np.dot(r, v) == pytest.approx(0, abs=1e-6)                  # vinkelrät: cirkulär bana


@pytest.mark.parametrize("inclination", [0.0, 51.6, 97.4])
def test_lvlh_basis_is_rotation_matrix(inclination):
    R = lvlh_basis(*circular_orbit_state(A, inclination))
    assert np.allclose(R.T @ R, np.eye(3))          # axlarna har längd 1 och är vinkelräta
    assert np.linalg.det(R) == pytest.approx(1.0)   # högerhänt system (inte spegelvänt)


def test_lvlh_axes_point_the_right_way():
    r, v = circular_orbit_state(A, 97.4)
    R = lvlh_basis(r, v)
    assert np.allclose(R[:, 0], r / np.linalg.norm(r))   # utåt = bort från jordens centrum
    assert np.allclose(R[:, 1], v / np.linalg.norm(v))   # framåt = hastighetens riktning


def test_round_trip_lvlh_eci_lvlh():
    r_ref, v_ref = circular_orbit_state(A, 97.4)
    rel = np.array([120.0, -3400.0, 55.0, 0.3, -1.1, 0.2])
    r, v = lvlh_to_eci(r_ref, v_ref, rel)
    assert np.allclose(eci_to_lvlh(r_ref, v_ref, r, v), rel)


def test_zero_relative_state_is_the_reference_point():
    r_ref, v_ref = circular_orbit_state(A, 97.4)
    r, v = lvlh_to_eci(r_ref, v_ref, np.zeros(6))
    assert np.allclose(r, r_ref)
    assert np.allclose(v, v_ref)


def test_standing_still_outward_means_moving_forward_in_eci():
    """Karusell-effekten: 1 km utåt och stilla i LVLH → n · 1000 m/s snabbare framåt i ECI."""
    r_ref, v_ref = circular_orbit_state(A, 97.4)
    r, v = lvlh_to_eci(r_ref, v_ref, [1000.0, 0, 0, 0, 0, 0])

    forward = lvlh_basis(r_ref, v_ref)[:, 1]
    extra_speed = np.dot(v - v_ref, forward)
    assert extra_speed == pytest.approx(mean_motion(A) * 1000.0)    # ≈ 1,107 m/s