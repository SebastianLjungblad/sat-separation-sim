import numpy as np
import pytest

from sepsim.analysis.conjunctions import closest_approach, pairwise_distances
from sepsim.constants import R_EARTH
from sepsim.dynamics.cw import cw_propagate, mean_motion

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