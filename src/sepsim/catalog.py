"""Satellitkatalog och hjälpfunktioner för att bygga ett uppdrag från appens inmatning.

Värdena är ungefärliga typvärden, avsedda som rimliga utgångspunkter. Alla går
att ändra i appen.
"""

from dataclasses import dataclass

from sepsim.scenario import Mission, Satellite


@dataclass(frozen=True)
class SatelliteType:
    mass: float               # [kg]
    area: float               # [m²] genomsnittlig tvärsnittsarea mot färdriktningen
    drag_coefficient: float   # [-]
    description: str


SATELLITE_TYPES: dict[str, SatelliteType] = {
    "3U CubeSat": SatelliteType(4.0, 0.03, 2.2, "10 × 10 × 34 cm, no deployed panels"),
    "6U CubeSat": SatelliteType(12.0, 0.06, 2.2, "10 × 22 × 34 cm, no deployed panels"),
    "12U CubeSat": SatelliteType(24.0, 0.12, 2.2, "22 × 22 × 34 cm, no deployed panels"),
    "Microsat with solar panels": SatelliteType(100.0, 4.0, 2.2, "large deployed solar panels, high drag"),
    "Compact smallsat": SatelliteType(200.0, 1.5, 2.2, "dense build, low drag per kg"),
    "Custom": SatelliteType(50.0, 0.5, 2.2, "enter your own values"),
}


@dataclass
class SatelliteInput:
    """En satellit som användaren har angett i appen."""
    name: str
    mass: float               # [kg]
    area: float               # [m²]
    drag_coefficient: float   # [-]
    separation_speed: float   # [m/s] fjäderns fart; omräknas till impuls = massa × fart


def mission_from_inputs(
    altitude_km: float,
    inclination_deg: float,
    stage_mass: float,
    stage_area: float,
    satellites: list[SatelliteInput],
) -> Mission:
    """
    Bygger ett uppdrag från appens inmatning. Riktningar och separationstider
    sätts till platshållare, eftersom det är dem optimeraren ska välja.
    Satelliterna släpps i den ordning de anges.
    """
    sats = [
        Satellite(
            name=s.name,
            mass=s.mass,
            spring_impulse=s.mass * s.separation_speed,
            direction=(1.0, 0.0, 0.0),
            t_sep=60.0 * k,
            area=s.area,
            drag_coefficient=s.drag_coefficient,
        )
        for k, s in enumerate(satellites)
    ]
    return Mission(
        altitude=altitude_km * 1000,
        stage_mass=stage_mass,
        satellites=sats,
        inclination_deg=inclination_deg,
        stage_area=stage_area,
    )