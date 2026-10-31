import numpy as np
import pytest

from sepsim.optimize import apply_plan, min_separation, optimize_plan
from sepsim.scenario import load_mission


def test_scenario1_is_unsafe():
    assert min_separation(load_mission("scenarios/scenario1.toml")) < 10.0


def test_scenario2_is_safe():
    assert min_separation(load_mission("scenarios/scenario2.toml")) > 100.0


def test_apply_plan_sets_directions_and_times():
    mission = load_mission("scenarios/scenario1.toml")
    params = [0, 0, 90, 0, 180, 0, 60, 90]  # framåt, utåt, bakåt; mellanrum 60 och 90 s
    planned = apply_plan(mission, params)

    assert [s.t_sep for s in planned.satellites] == [0.0, 60.0, 150.0]
    assert np.allclose(planned.satellites[0].direction, (0, 1, 0), atol=1e-12)
    assert np.allclose(planned.satellites[1].direction, (1, 0, 0), atol=1e-12)
    assert np.allclose(planned.satellites[2].direction, (0, -1, 0), atol=1e-12)


def test_apply_plan_keeps_masses_and_does_not_change_original():
    mission = load_mission("scenarios/scenario1.toml")
    original_direction = mission.satellites[0].direction
    planned = apply_plan(mission, [0, 0, 90, 0, 180, 0, 60, 90])

    assert [s.mass for s in planned.satellites] == [s.mass for s in mission.satellites]
    assert mission.satellites[0].direction == original_direction  # originalet orört


def test_optimizer_beats_naive_plan():
    mission = load_mission("scenarios/scenario1.toml")
    best_mission, best_score = optimize_plan(
        mission, maxiter=20
    )  # kort körning för testet

    assert best_score > 100.0
    assert best_score > min_separation(mission)
    assert best_score == pytest.approx(min_separation(best_mission))  # betyget stämmer
