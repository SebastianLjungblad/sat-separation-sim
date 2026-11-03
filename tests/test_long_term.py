import numpy as np
import pytest

from sepsim.analysis.long_term import LongTermResult, RobustRow, long_term_min_separation, rank_robust
from sepsim.dynamics.forces import ForceModel
from sepsim.optimize import min_separation
from sepsim.scenario import load_mission

TWO_BODY = ForceModel(j2=False, drag=False)


def test_long_term_agrees_with_cw_over_short_time():
    """Över 2,4 timmar och utan störningar ska den numeriska långtidsanalysen ge samma svar som CW."""
    mission = load_mission("scenarios/scenario1.toml")
    numerical = long_term_min_separation(mission, days=0.1, model=TWO_BODY, n_samples=3000)
    cw = min_separation(mission, n_orbits=1.5, n_samples=3000)
    assert numerical.min_distance == pytest.approx(cw, abs=1.0)


def test_long_term_reports_worst_pair_and_time():
    mission = load_mission("scenarios/scenario1.toml")
    result = long_term_min_separation(mission, days=0.1, model=TWO_BODY, n_samples=3000)
    assert "–" in result.worst_pair
    assert 0 < result.time_days <= 0.1


def test_worst_case_takes_the_smallest_value():
    row = RobustRow(
        mission=None,
        cw_score=700.0,
        results={
            "low": LongTermResult(800.0, "A–B", 1.0),
            "medium": LongTermResult(300.0, "A–B", 2.0),
            "high": LongTermResult(500.0, "A–B", 1.5),
        },
    )
    assert row.worst_case == 300.0


def test_rank_robust_sorts_by_worst_case():
    mission = load_mission("scenarios/scenario2.toml")
    candidates = [(mission, 5.0), (mission, 1000.0)]        # samma plan, olika CW-betyg
    rows = rank_robust(candidates, days=0.05, levels=("medium",), workers=1)
    assert rows[0].worst_case >= rows[1].worst_case
    assert rows[1].worst_case == 5.0                        # CW-betyget räknas in i sämsta fallet