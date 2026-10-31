import math

from sepsim.constants import MU_EARTH, R_EARTH


def test_orbital_period_500km():
    altitude = 500e3  # [m] 500 km
    a = R_EARTH + altitude  # [m] banradie för en cirkulär bana

    period = 2 * math.pi * math.sqrt(a**3 / MU_EARTH)  # [s] T = 2π·√(a³/μ)
    period_min = period / 60

    assert 94 < period_min < 95
