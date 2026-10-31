import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Satellite:
    name: str
    mass: float  # [kg]
    spring_impulse: float  # [N·s]
    direction: tuple[float, float, float]  # LVLH, behöver inte vara normerad
    t_sep: float  # [s] separationstid


@dataclass
class Mission:
    altitude: float  # [m] banhöjd
    stage_mass: float  # [kg] raketsteg + dispenser, utan satelliter
    satellites: list[Satellite]


def load_mission(path: str | Path) -> Mission:
    """Läser ett scenario från en TOML-fil. Omvandlar km → m."""
    with open(path, "rb") as f:
        data = tomllib.load(f)

    satellites = [
        Satellite(
            name=s["name"],
            mass=s["mass_kg"],
            spring_impulse=s["spring_impulse_Ns"],
            direction=tuple(s["direction"]),
            t_sep=s["t_sep_s"],
        )
        for s in data["satellites"]
    ]

    return Mission(
        altitude=data["altitude_km"] * 1000,
        stage_mass=data["stage_mass_kg"],
        satellites=satellites,
    )
