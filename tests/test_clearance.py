import numpy as np

from sepsim.analysis.conjunctions import closest_approach, pairwise_distances
from sepsim.constants import R_EARTH
from sepsim.dynamics.cw import mean_motion
from sepsim.dynamics.separation import propagate_mission, release_times
from sepsim.scenario import Mission, Satellite

N = mean_motion(R_EARTH + 500e3)
T = 2 * np.pi / N
t = np.linspace(0, 1.5 * T, 5000)
CLEARANCE = 600.0


def late_separation_mission() -> Mission:
    """Sat 2 släpps först efter 15 minuter, alltså efter den gamla frigångstiden."""
    return Mission(
        altitude=500e3,
        stage_mass=1200.0,
        satellites=[
            Satellite(
                "Sat 1",
                mass=150.0,
                spring_impulse=150.0,
                direction=(0, 1, 0),
                t_sep=0.0,
            ),
            Satellite(
                "Sat 2",
                mass=150.0,
                spring_impulse=150.0,
                direction=(0, -1, 0),
                t_sep=900.0,
            ),
        ],
    )


def test_release_times_in_propagation_order():
    mission = late_separation_mission()
    mission.satellites.reverse()  # ordningen i filen ska inte spela roll
    assert np.allclose(release_times(mission), [0.0, 0.0, 900.0])


def test_closest_approach_accepts_one_clearance_per_pair():
    t_short = np.array([0.0, 600.0, 1200.0, 1800.0, 5700.0])
    distances = np.array(
        [
            [1.0, 120.0, 450.0, 300.0, 2.0],
            [1.0, 200.0, 900.0, 1600.0, 2500.0],
        ]
    )
    min_dist, t_min = closest_approach(distances, t_short, after=[600.0, 1200.0])

    assert np.allclose(min_dist, [2.0, 900.0])
    assert np.allclose(t_min, [5700.0, 1200.0])


def test_late_separation_is_not_a_false_collision():
    """En sen separation ska inte se ut som en krock när frigångstiden räknas per par."""
    mission = late_separation_mission()
    names, states = propagate_mission(mission, N, t)
    pairs, distances = pairwise_distances(states[:, :, :3])
    stage_sat2 = pairs.index((0, 2))

    # Gammal metod: samma frigångstid för alla par → Sat 2 sitter vid steget vid 900 s
    old_min, _ = closest_approach(distances, t, after=CLEARANCE)
    assert old_min[stage_sat2] < 1.0

    # Ny metod: frigångstid räknad från den senare separationen i varje par
    release = release_times(mission)
    after = [max(release[i], release[j]) + CLEARANCE for i, j in pairs]
    new_min, _ = closest_approach(distances, t, after=after)
    assert new_min[stage_sat2] > 100.0
