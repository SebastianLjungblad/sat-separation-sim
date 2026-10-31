from sepsim.scenario import load_mission


def test_load_scenario1():
    mission = load_mission("scenarios/scenario1.toml")

    assert mission.altitude == 500_000
    assert mission.stage_mass == 1200
    assert len(mission.satellites) == 3
    assert mission.satellites[0].name == "Sat 1"
    assert mission.satellites[0].mass == 150
    assert mission.satellites[2].direction == (1, 0, 1)
