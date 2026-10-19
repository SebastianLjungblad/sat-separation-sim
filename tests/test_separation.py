import numpy as np
import pytest

from sepsim.dynamics.separation import separation_kicks
from sepsim.scenario import Mission, Satellite


def make_mission(stage_mass: float = 1200.0) -> Mission:
    """Tre lika satelliter, släppta i olika riktningar med en minuts mellanrum."""
    return Mission(
        altitude=500e3,
        stage_mass=stage_mass,
        satellites=[
            Satellite("Sat 1", mass=150.0, spring_impulse=120.0, direction=(1, 0, 0), t_sep=0.0),
            Satellite("Sat 2", mass=150.0, spring_impulse=120.0, direction=(0, 1, 0), t_sep=60.0),
            Satellite("Sat 3", mass=150.0, spring_impulse=120.0, direction=(0, 1, 1), t_sep=120.0),
        ],
    )


def test_momentum_is_conserved_at_each_separation():
    """Satellitens rörelsemängd + stackens rörelsemängd = 0 vid varje separation."""
    mission = make_mission()
    kicks = separation_kicks(mission)

    for k, (sat, dv_sat, dv_stack) in enumerate(kicks):
        m_rest = mission.stage_mass + sum(s.mass for s, _, _ in kicks[k + 1:])
        total_momentum = sat.mass * dv_sat + m_rest * dv_stack
        assert np.allclose(total_momentum, 0)


def test_satellite_speed_is_impulse_over_mass():
    """Satellitens fart = J / m, oavsett hur riktningen är skriven."""
    for sat, dv_sat, _ in separation_kicks(make_mission()):
        assert np.linalg.norm(dv_sat) == pytest.approx(sat.spring_impulse / sat.mass)


def test_stack_recoils_opposite_to_satellite():
    """Stacken får rekyl rakt mot satellitens riktning."""
    for _, dv_sat, dv_stack in separation_kicks(make_mission()):
        cos_angle = np.dot(dv_sat, dv_stack) / (np.linalg.norm(dv_sat) * np.linalg.norm(dv_stack))
        assert cos_angle == pytest.approx(-1.0)


def test_recoil_grows_as_stack_gets_lighter():
    """Stacken blir lättare för varje separation → rekylen blir större."""
    kicks = separation_kicks(make_mission())
    recoil_speeds = [np.linalg.norm(dv_stack) for _, _, dv_stack in kicks]

    assert recoil_speeds[0] < recoil_speeds[1] < recoil_speeds[2]
    assert recoil_speeds[0] == pytest.approx(120.0 / 1500.0)   # steg + 2 satelliter kvar
    assert recoil_speeds[2] == pytest.approx(120.0 / 1200.0)   # bara steget kvar


def test_heavy_stage_gives_no_recoil():
    """Ett extremt tungt steg rör sig inte → samma situation som i v0.1."""
    for _, _, dv_stack in separation_kicks(make_mission(stage_mass=1e12)):
        assert np.allclose(dv_stack, 0)


def test_kicks_are_returned_in_separation_order():
    """Satelliterna sorteras efter t_sep även om de anges i annan ordning."""
    mission = make_mission()
    mission.satellites.reverse()

    names = [sat.name for sat, _, _ in separation_kicks(mission)]
    assert names == ["Sat 1", "Sat 2", "Sat 3"]