import numpy as np
import pytest

from sepsim.constants import R_EARTH
from sepsim.dynamics.cw import mean_motion, propagate_with_separation
from sepsim.dynamics.separation import propagate_mission, separation_kicks
from sepsim.scenario import Mission, Satellite

N = mean_motion(R_EARTH + 500e3)
T = 2 * np.pi / N
t = np.linspace(0, 1.5 * T, 3000)


def make_mission(stage_mass: float = 1200.0) -> Mission:
    """Tre satelliter med olika massor, släppta i olika riktningar."""
    return Mission(
        altitude=500e3,
        stage_mass=stage_mass,
        satellites=[
            Satellite("Sat 1", mass=150.0, spring_impulse=120.0, direction=(1, 0, 0), t_sep=0.0),
            Satellite("Sat 2", mass=80.0, spring_impulse=120.0, direction=(0, 1, 0), t_sep=60.0),
            Satellite("Sat 3", mass=200.0, spring_impulse=120.0, direction=(1, -1, 1), t_sep=120.0),
        ],
    )


def test_output_shape_and_names():
    """Ett objekt per satellit plus steget, en rad per tidpunkt, sex värden per rad."""
    names, states = propagate_mission(make_mission(), N, t)

    assert names == ["Stage", "Sat 1", "Sat 2", "Sat 3"]
    assert states.shape == (4, len(t), 6)


def test_heavy_stage_matches_v01():
    """Extremt tungt steg → ingen rekyl → samma resultat som v0.1."""
    mission = make_mission(stage_mass=1e12)
    _, states = propagate_mission(mission, N, t)

    # Steget står kvar i origo (inom 1 mm; rekylen är ~1e-10 m/s men driver lite över 1,5 varv)
    assert np.allclose(states[0], 0, atol=1e-3)

    # Varje satellit följer samma bana som med propagate_with_separation direkt
    for k, (sat, dv_sat, _) in enumerate(separation_kicks(mission)):
        expected = propagate_with_separation([0, 0, 0, *dv_sat], N, t, sat.t_sep)
        assert np.allclose(states[k + 1], expected, atol=1e-3)


def test_center_of_mass_stays_at_origin():
    """Fjädrarna är inre krafter → det massviktade medelvärdet rör sig aldrig."""
    mission = make_mission()
    _, states = propagate_mission(mission, N, t)

    weighted_sum = mission.stage_mass * states[0]
    for k, sat in enumerate(sorted(mission.satellites, key=lambda s: s.t_sep)):
        weighted_sum = weighted_sum + sat.mass * states[k + 1]

    # Gäller både positioner och hastigheter, vid alla tidpunkter
    assert np.allclose(weighted_sum, 0, atol=1e-6)


def test_satellite_moves_with_stage_before_separation():
    """Före sin separation sitter satelliten fast → samma tillstånd som steget."""
    mission = make_mission()
    _, states = propagate_mission(mission, N, t)

    for k, sat in enumerate(sorted(mission.satellites, key=lambda s: s.t_sep)):
        attached = t < sat.t_sep
        assert np.allclose(states[k + 1][attached], states[0][attached])


def test_stage_drifts_because_of_recoil():
    """Med ett realistiskt steg flyttar rekylen steget märkbart bort från origo."""
    _, states = propagate_mission(make_mission(), N, t)

    final_distance = np.linalg.norm(states[0, -1, :3])
    assert final_distance > 100.0     # [m] efter 1,5 varv