"""Fysikaliska konstanter. Alla värden i SI-enheter."""

# --- Jorden: gravitation ---
MU_EARTH = (
    3.986004418e14  # [m^3/s^2] Gravitationsparameter GM. Källa: WGS84            (v1)
)
R_EARTH = (
    6378137.0  # [m] Ekvatorsradie. Källa: WGS84                               (v1)
)
J2 = 1.0826267e-3  # [-] Tillplattning, ONORMALISERAD. Källa: EGM2008 via Vallado  (v2)
J3 = -2.5324e-6  # [-] Päronform (nord/syd-asymmetri). Källa: EGM2008            (bonus)
J4 = -1.6199e-6  # [-] Högre ordningens zonal term. Källa: EGM2008               (bonus)

# --- Jorden: rotation och form ---
OMEGA_EARTH = 7.292115e-5  # [rad/s] Rotationshastighet. Källa: WGS84                      (v2: luftmotstånd)
FLATTENING = (
    1 / 298.257223563
)  # [-] Geometrisk tillplattning. Källa: WGS84                    (tillägg: Esrange)

# --- Fundamentala konstanter ---
SPEED_OF_LIGHT = 299_792_458.0  # [m/s] Exakt per definition (SI)
AU = 149_597_870_700.0  # [m] Astronomisk enhet. Exakt per definition (IAU 2012)

# --- Solen ---
SOLAR_FLUX = 1361.0  # [W/m^2] Solarkonstanten vid 1 AU. Källa: IAU 2015 Resolution B3
SOLAR_PRESSURE = (
    SOLAR_FLUX / SPEED_OF_LIGHT
)  # [N/m^2] Härledd: strålningstryck vid 1 AU (v2+)
MU_SUN = 1.32712440018e20  # [m^3/s^2] Källa: IAU / JPL                                    (bonus)

# --- Månen ---
MU_MOON = 4.9028001e12  # [m^3/s^2] Källa: JPL DE430                                    (bonus)
