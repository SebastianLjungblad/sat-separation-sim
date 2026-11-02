import numpy as np
import pytest

from sepsim.constants import MU_EARTH, R_EARTH
from sepsim.dynamics.cw import mean_motion
from sepsim.dynamics.forces import ForceModel
from sepsim.dynamics.frames import circular_orbit_state
from sepsim.dynamics.propagator import integrate, propagate_mission_numerical
from sepsim.dynamics.separation import propagate_mission
from sepsim.scenario import Mission, Satellite

A = R_EARTH + 500e3
N = mean_motion(A)
T = 2 * np.pi / N
TWO_BODY = ForceModel(j2=False, drag=False)


def make_mission(speed_scale: float = 1.0) -> Mission:
    return Mission(
        altitude=500e3,
        stage_mass=1200.0,
        satellites=[
            Satellite("Sat 1", 150.0, 150.0 * speed_scale, (1, 0.5, -0.3), 0.0),
            Satellite("Sat 2", 150.0, 150.0 * speed_scale, (0.9, 0.1, 0.4), 120.0),
        ],
    )


def test_circular_orbit_stays_circular_with_two_body():
    """Utan störningar ska en cirkulär bana behålla radien och komma tillbaka efter ett varv."""
    r0, v0 = circular_orbit_state(A, 97.4)
    t = np.linspace(0, T, 200)
    states = integrate(np.concatenate([r0, v0]), 0.0, t, 0.0, TWO_BODY)

    radii = np.linalg.norm(states[:, :3], axis=1)
    assert np.allclose(radii, A, atol=1e-3)                  # inom 1 mm
    assert np.allclose(states[-1, :3], r0, atol=1e-2)       # tillbaka efter ett varv


def test_energy_is_conserved_with_two_body():
    r0, v0 = circular_orbit_state(A, 51.6)
    v0 = v0 * 1.01                                           # lite elliptisk bana
    t = np.linspace(0, 3 * T, 300)
    states = integrate(np.concatenate([r0, v0]), 0.0, t, 0.0, TWO_BODY)

    energy = 0.5 * np.sum(states[:, 3:] ** 2, axis=1) - MU_EARTH / np.linalg.norm(states[:, :3], axis=1)
    assert np.max(np.abs(energy - energy[0])) / abs(energy[0]) < 1e-10


def test_numerical_two_body_matches_cw_for_small_separations():
    """Små knuffar → CW:s förenkling är nästan exakt → samma banor inom några cm."""
    mission = make_mission(speed_scale=0.01)                 # 1 cm/s i stället för 1 m/s
    t = np.linspace(0, 1.5 * T, 400)
    _, numerical = propagate_mission_numerical(mission, t, TWO_BODY)
    _, cw = propagate_mission(mission, N, t)
    assert np.max(np.abs(numerical[:, :, :3] - cw[:, :, :3])) < 0.05


def test_cw_error_grows_with_square_of_separation():
    """CW:s förenkling ger ett fel som växer med kvadraten på avståndet."""
    t = np.linspace(0, 1.5 * T, 400)
    errors = []
    for scale in [0.1, 1.0]:
        mission = make_mission(speed_scale=scale)
        _, numerical = propagate_mission_numerical(mission, t, TWO_BODY)
        _, cw = propagate_mission(mission, N, t)
        errors.append(np.max(np.abs(numerical[:, :, :3] - cw[:, :, :3])))
    assert errors[1] / errors[0] == pytest.approx(100, rel=0.2)   # 10 × knuff → 100 × fel


def test_satellite_is_attached_before_separation():
    mission = make_mission()
    t = np.linspace(0, 1.5 * T, 400)
    _, states = propagate_mission_numerical(mission, t, ForceModel())
    attached = t < 120.0
    assert np.allclose(states[2][attached], states[0][attached])


def test_drag_makes_lighter_object_drift_ahead():
    """Ett objekt med större area/massa bromsas mer, sjunker och drar ifrån FRAMÅT."""
    mission = Mission(
        altitude=500e3,
        stage_mass=1200.0,
        satellites=[
            Satellite("Light", 50.0, 1e-6, (1, 0, 0), 0.0, area=2.0),   # nästan ingen knuff
        ],
        stage_area=1.0,                                     # kompakt steg, lite drag
    )
    t = np.linspace(0, 86400, 500)                          # ett dygn
    _, states = propagate_mission_numerical(mission, t, ForceModel(j2=False, drag=True))
    along_track_gap = states[1, -1, 1] - states[0, -1, 1]
    assert along_track_gap > 100.0                          # satelliten ligger framför steget