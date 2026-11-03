import pytest

from sepsim.catalog import SATELLITE_TYPES, SatelliteInput, mission_from_inputs


def test_catalog_values_are_physical():
    for name, t in SATELLITE_TYPES.items():
        assert t.mass > 0 and t.area > 0, name
        assert 1.0 <= t.drag_coefficient <= 4.0, name


def test_mission_from_inputs():
    sats = [
        SatelliteInput("A", mass=100.0, area=4.0, drag_coefficient=2.2, separation_speed=1.0),
        SatelliteInput("B", mass=12.0, area=0.06, drag_coefficient=2.2, separation_speed=0.5),
    ]
    mission = mission_from_inputs(450, 51.6, 1500.0, 8.0, sats)

    assert mission.altitude == 450_000
    assert mission.inclination_deg == 51.6
    assert mission.stage_mass == 1500.0 and mission.stage_area == 8.0
    assert [s.name for s in mission.satellites] == ["A", "B"]
    assert mission.satellites[1].spring_impulse == pytest.approx(6.0)     # 12 kg × 0,5 m/s
    assert mission.satellites[0].area == 4.0
    assert [s.t_sep for s in mission.satellites] == [0.0, 60.0]           # släpps i angiven ordnings