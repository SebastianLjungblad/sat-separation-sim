import numpy as np
import pytest

from sepsim.analysis.conjunctions import closest_approach, pairwise_distances
from sepsim.constants import R_EARTH
from sepsim.dynamics.cw import cw_propagate, mean_motion, propagate_with_separation


A = R_EARTH + 500e3
N = mean_motion(A)
T = 2 * np.pi / N
t = np.linspace(0, 1.5 * T, 5000)


def positions_from_states(states0):
    """Hjälpfunktion: dispensern i origo + en satellit per starttillstånd."""
    dispenser = np.zeros((len(t), 3))
    sats = [cw_propagate(s, N, t)[:, :3] for s in states0]
    return np.stack([dispenser, *sats])


def test_radial_push_detects_recontact_after_one_orbit():
    """Radiell knuff → satelliten kommer tillbaka till dispensern efter ett varv."""
    positions = positions_from_states([[0, 0, 0, 1.0, 0, 0]])
    pairs, distances = pairwise_distances(positions)
    min_dist, t_min = closest_approach(distances, t, after=600)

    assert pairs == [(0, 1)]
    assert min_dist[0] < 1.0                       # närmare än 1 m
    assert t_min[0] == pytest.approx(T, rel=0.01)  # inom 1 % av ett varv

def test_separation_time_shifts_trajectory():
    """Satellit släppt vid 300 s = samma bana som släppt vid 0 s, förskjuten 300 s."""
    state0 = [0, 0, 0, 1.0, 0, 0]
    t = np.linspace(0, 2000, 2001)            # var 1:a sekund

    delayed = propagate_with_separation(state0, N, t, t_sep=300)
    immediate = cw_propagate(state0, N, t)

    # 1. Före separationen: allt är noll
    assert np.allclose(delayed[t < 300], 0)

    # 2. Efter: samma bana, förskjuten 300 s
    #    delayed vid t = 300 + k  ska vara lika med  immediate vid t = k
    assert np.allclose(delayed[300:], immediate[:-300])