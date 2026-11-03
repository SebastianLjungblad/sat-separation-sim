"""Tester för exporten till 3D-visaren."""

import json
from datetime import datetime, timezone

import numpy as np
import pytest

from sepsim.constants import R_EARTH
from sepsim.dynamics.forces import ForceModel
from sepsim.dynamics.frames import circular_orbit_state
from sepsim.dynamics.propagator import integrate, propagate_mission_eci
from sepsim.export import (decode, export_trajectories, gmst, hermite, raan_for_ltan, rotate_z,
                           sample_times, sun_direction)
from sepsim.scenario import load_mission

MISSION = load_mission("scenarios/scenario3_mixed_robust.toml")


def test_gmst_at_j2000():
    # GMST 2000-01-01 12:00 UT1 = 280.46061837° (IAU 1982)
    when = datetime(2000, 1, 1, 12, tzinfo=timezone.utc)
    assert np.degrees(gmst(when)) == pytest.approx(280.46061837, abs=1e-6)


def test_sun_at_march_equinox_points_along_x():
    # Vårdagjämningen 2027-03-20 20:25 UTC: solen står i vårdagjämningspunkten, ECI:s x-axel
    sun = sun_direction(datetime(2027, 3, 20, 20, 25, tzinfo=timezone.utc))
    assert np.degrees(np.arccos(sun[0])) < 0.05


def test_ltan_noon_puts_node_under_the_sun():
    when = datetime(2027, 6, 1, tzinfo=timezone.utc)
    sun = sun_direction(when)
    raan = raan_for_ltan(when, 12.0)
    assert raan == pytest.approx(np.arctan2(sun[1], sun[0]))


def test_rotation_about_earth_axis_commutes_with_dynamics():
    # Att vrida starttillståndet och sedan propagera = att propagera och sedan vrida
    r0, v0 = circular_orbit_state(R_EARTH + 500e3, 97.4)
    state0 = np.concatenate([r0, v0])
    t = np.linspace(0, 86400, 50)
    model = ForceModel(j2=True, drag=True)
    angle = np.radians(123.0)
    a = integrate(rotate_z(state0, angle), 0.0, t, 2.2 * 4 / 100, model)
    b = rotate_z(integrate(state0, 0.0, t, 2.2 * 4 / 100, model), angle)
    assert np.max(np.abs(a[:, :3] - b[:, :3])) < 1e-3          # under en millimeter efter ett dygn


def test_sample_times_include_point_just_before_each_separation():
    t = sample_times(MISSION, days=0.1, step=60.0)
    for sat in MISSION.satellites:
        if sat.t_sep > 0:
            assert sat.t_sep in t
            assert np.any(np.isclose(t, sat.t_sep - 1e-3))


def test_hermite_relative_distance_error_below_one_centimetre():
    # Interpolera 60 s-punkter och jämför med en direkt propagering var tionde sekund
    days = 0.5
    coarse = sample_times(MISSION, days, 60.0)
    _, eci_coarse, _ = propagate_mission_eci(MISSION, coarse)
    fine = np.arange(0.0, days * 86400.0, 10.0)
    _, eci_fine, _ = propagate_mission_eci(MISSION, fine)

    interp = np.stack([hermite(fine, coarse, eci_coarse[k]) for k in range(eci_coarse.shape[0])])
    absolute_error = np.linalg.norm(interp - eci_fine[:, :, :3], axis=2)
    assert absolute_error.max() < 1.0                           # absolut: under en meter
    for i in range(len(interp)):
        for j in range(i + 1, len(interp)):
            d_interp = np.linalg.norm(interp[i] - interp[j], axis=1)
            d_true = np.linalg.norm(eci_fine[i, :, :3] - eci_fine[j, :, :3], axis=1)
            assert np.max(np.abs(d_interp - d_true)) < 0.01     # relativt: under en centimeter


def test_export_is_json_and_round_trips():
    data = export_trajectories(MISSION, days=0.2, step=60.0)
    text = json.dumps(data)
    back = json.loads(text)
    t = decode(back["t_s"])
    assert len(back["objects"]) == 1 + len(MISSION.satellites)
    for obj in back["objects"]:
        state = decode(obj["state"], 6)
        assert state.shape == (len(t), 6)
        altitude = np.linalg.norm(state[:, :3], axis=1) - R_EARTH
        assert np.all(np.abs(altitude - 500e3) < 30e3)
    assert back["closest_passes"][0]["distance_m"] <= back["closest_passes"][-1]["distance_m"]