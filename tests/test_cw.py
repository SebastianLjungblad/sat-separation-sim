import numpy as np
import pytest

from sepsim.constants import R_EARTH
from sepsim.dynamics.cw import (
    cw_propagate,
    mean_motion,
    propagate_with_separation,
    separation_state,
)

A = R_EARTH + 500e3  # [m] cirkulär bana på 500 km höjd
N = mean_motion(A)  # [rad/s]
T = 2 * np.pi / N  # [s] omloppstid


def test_radial_push_returns_after_one_orbit():
    """Knuff rakt utåt → satelliten är tillbaka vid dispensern efter ett varv."""
    state0 = [0, 0, 0, 1.0, 0, 0]  # 1 m/s radiellt
    x, y, z = cw_propagate(state0, N, T)[0, :3]

    assert x == pytest.approx(0, abs=1e-6)
    assert y == pytest.approx(0, abs=1e-6)
    assert z == pytest.approx(0, abs=1e-6)


def test_along_track_push_drifts_behind():
    """Knuff framåt → satelliten hamnar 6π/n BAKOM dispensern efter ett varv."""
    state0 = [0, 0, 0, 0, 1.0, 0]  # 1 m/s framåt
    x, y, _ = cw_propagate(state0, N, T)[0, :3]

    assert x == pytest.approx(0, abs=1e-6)
    assert y == pytest.approx(-6 * np.pi / N, rel=1e-9)
    assert y < -15_000  # ca −17 km: bakom, inte framför


def test_cross_track_is_pure_oscillation():
    """Knuff tvärs banan → svängning i z, ingen påverkan på x och y."""
    state0 = [0, 0, 0, 0, 0, 1.0]
    states = cw_propagate(state0, N, np.linspace(0, T, 200))

    assert np.allclose(states[:, 0], 0)  # x förblir 0
    assert np.allclose(states[:, 1], 0)  # y förblir 0
    assert np.max(np.abs(states[:, 2])) == pytest.approx(1.0 / N, rel=1e-3)


def test_separation_time_shifts_trajectory():
    """Satellit släppt vid 300 s = samma bana som släppt vid 0 s, förskjuten 300 s."""
    state0 = [0, 0, 0, 1.0, 0, 0]
    t = np.linspace(0, 2000, 2001)  # var 1:a sekund

    delayed = propagate_with_separation(state0, N, t, t_sep=300)
    immediate = cw_propagate(state0, N, t)

    # 1. Före separationen: allt är noll
    assert np.allclose(delayed[t < 300], 0)

    # 2. Efter: samma bana, förskjuten 300 s
    #    delayed vid t = 300 + k  ska vara lika med  immediate vid t = k
    assert np.allclose(delayed[300:], immediate[:-300])

    def test_separation_state_has_requested_speed():
        state = separation_state([3, 4, 0], speed=2.0)
        assert np.allclose(state[:3], 0)  # startar i dispensern
        assert np.linalg.norm(state[3:]) == pytest.approx(2.0)  # rätt fart
        assert np.allclose(state[3:], [1.2, 1.6, 0])  # rätt riktning
