import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Satellite:
    name: str
    mass: float                              # [kg]
    spring_impulse: float                    # [N·s]
    direction: tuple[float, float, float]    # LVLH, behöver inte vara normerad
    t_sep: float                             # [s] separationstid
    area: float = 1.0                        # [m²] tvärsnittsarea, för luftmotstånd (v0.4)
    drag_coefficient: float = 2.2            # [-] Cd (v0.4)


@dataclass
class Mission:
    altitude: float                          # [m] banhöjd
    stage_mass: float                        # [kg] raketsteg + dispenser, utan satelliter
    satellites: list[Satellite]
    inclination_deg: float = 97.4            # [°] banans lutning mot ekvatorn (v0.4)
    stage_area: float = 10.0                 # [m²] stegets tvärsnittsarea (v0.4)
    stage_drag_coefficient: float = 2.2      # [-] stegets Cd (v0.4)


def load_mission(path: str | Path) -> Mission:
    with open(path, "rb") as f:
        data = tomllib.load(f)
    satellites = [
        Satellite(
            name=s["name"],
            mass=s["mass_kg"],
            spring_impulse=s["spring_impulse_Ns"],
            direction=tuple(s["direction"]),
            t_sep=s["t_sep_s"],
            area=s.get("area_m2", 1.0),
            drag_coefficient=s.get("drag_coefficient", 2.2),
        )
        for s in data["satellites"]
    ]
    return Mission(
        altitude=data["altitude_km"] * 1000,
        stage_mass=data["stage_mass_kg"],
        satellites=satellites,
        inclination_deg=data.get("inclination_deg", 97.4),
        stage_area=data.get("stage_area_m2", 10.0),
        stage_drag_coefficient=data.get("stage_drag_coefficient", 2.2),
    )


def mission_to_toml(mission: Mission, name: str) -> str:
    """Uppdraget som TOML-text, i samma format som load_mission läser."""
    import numpy as np

    lines = [
        f'name = "{name}"',
        f"altitude_km = {mission.altitude / 1000:g}",
        f"stage_mass_kg = {mission.stage_mass:g}",
        f"inclination_deg = {mission.inclination_deg:g}",
        f"stage_area_m2 = {mission.stage_area:g}",
        f"stage_drag_coefficient = {mission.stage_drag_coefficient:g}",
    ]
    for sat in mission.satellites:
        d = np.asarray(sat.direction, dtype=float) / np.linalg.norm(sat.direction)
        az = np.degrees(np.arctan2(d[0], d[1]))
        el = np.degrees(np.arcsin(d[2]))
        lines += [
            "",
            "[[satellites]]",
            f'name = "{sat.name}"',
            f"mass_kg = {sat.mass:g}",
            f"spring_impulse_Ns = {sat.spring_impulse:g}",
            f"area_m2 = {sat.area:g}",
            f"drag_coefficient = {sat.drag_coefficient:g}",
            f"direction = [{d[0]:.6f}, {d[1]:.6f}, {d[2]:.6f}]     # azimuth {az:.1f}°, elevation {el:.1f}°",
            f"t_sep_s = {sat.t_sep:.1f}",
        ]
    return "\n".join(lines) + "\n"


def save_mission(mission: Mission, path: str | Path, name: str) -> None:
    """Sparar uppdraget som en TOML-fil i samma format som load_mission läser."""
    Path(path).write_text(mission_to_toml(mission, name))