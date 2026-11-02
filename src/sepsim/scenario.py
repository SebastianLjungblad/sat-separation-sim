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