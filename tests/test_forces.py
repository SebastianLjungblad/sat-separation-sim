import numpy as np
import pytest

from sepsim.constants import J2, MU_EARTH, R_EARTH
from sepsim.dynamics.forces import (
    ForceModel,
    accel_drag,
    accel_j2,
    accel_two_body,
    atmospheric_density,
    total_acceleration,
)
from sepsim.dynamics.frames import circular_orbit_state

A = R_EARTH + 500e3


def test_two_body_points_to_earth_center_with_mu_over_r2():
    r = np.array([A, 0.0, 0.0])
    a = accel_two_body(r)
    assert np.linalg.norm(a) == pytest.approx(MU_EARTH / A**2)       # ≈ 8,43 m/s²
    assert np.allclose(a / np.linalg.norm(a), [-1, 0, 0])            # rakt mot centrum


def test_j2_pulls_inward_at_equator():
    """Över ekvatorn drar den extra massan i ekvatorbulan satelliten inåt."""
    a = accel_j2(np.array([A, 0.0, 0.0]))
    expected = 1.5 * J2 * MU_EARTH * R_EARTH**2 / A**4
    assert a[0] == pytest.approx(-expected)
    assert np.allclose(a[1:], 0)


def test_j2_pushes_outward_over_pole():
    """Över polen ligger bulan 'under' satelliten åt sidorna → netto mindre dragning, alltså utåt."""
    a = accel_j2(np.array([0.0, 0.0, A]))
    assert a[2] > 0
    assert np.allclose(a[:2], 0)


def test_j2_is_about_a_thousandth_of_gravity():
    ratio = np.linalg.norm(accel_j2(np.array([A, 0.0, 0.0]))) / np.linalg.norm(accel_two_body(np.array([A, 0.0, 0.0])))
    assert 1e-3 < ratio < 2e-3


def test_density_decreases_with_altitude_and_scales_with_solar_activity():
    assert atmospheric_density(450e3) > atmospheric_density(500e3) > atmospheric_density(550e3)
    assert atmospheric_density(500e3, "high") > atmospheric_density(500e3, "medium") > atmospheric_density(500e3, "low")


def test_drag_opposes_motion_and_has_expected_size():
    r, v = circular_orbit_state(A, 97.4)
    cd_am = 2.2 * 1.2 / 150.0                    # Cd · A / m för en satellit på 150 kg med 1,2 m²
    a = accel_drag(r, v, cd_am)

    assert np.dot(a, v) < 0                      # bromsar
    assert 1e-8 < np.linalg.norm(a) < 1e-5       # pyttelitet jämfört med gravitationen


def test_force_model_switches():
    r, v = circular_orbit_state(A, 97.4)
    only_gravity = total_acceleration(r, v, 0.02, ForceModel(j2=False, drag=False))
    assert np.allclose(only_gravity, accel_two_body(r))

    with_j2 = total_acceleration(r, v, 0.02, ForceModel(j2=True, drag=False))
    assert np.allclose(with_j2, accel_two_body(r) + accel_j2(r))