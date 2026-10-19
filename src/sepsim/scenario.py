from dataclasses import dataclass


@dataclass
class Satellite:
    name: str
    mass: float                              # [kg]
    spring_impulse: float                    # [N·s]
    direction: tuple[float, float, float]    # LVLH, behöver inte vara normerad
    t_sep: float                             # [s] separationstid


@dataclass
class Mission:
    altitude: float                          # [m] banhöjd
    stage_mass: float                        # [kg] raketsteg + dispenser, utan satelliter
    satellites: list[Satellite]