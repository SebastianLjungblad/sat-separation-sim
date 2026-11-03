"""sepsim – satellite separation planner (Streamlit app).

Starta med:
    uv run streamlit run app/streamlit_app.py
"""

import pandas as pd
import streamlit as st

from sepsim.catalog import SATELLITE_TYPES, SatelliteInput, mission_from_inputs

st.set_page_config(page_title="sepsim – satellite separation planner", page_icon="🛰️", layout="wide")

DEFAULT_TYPES = ["Microsat with solar panels", "6U CubeSat", "Compact smallsat", "12U CubeSat", "3U CubeSat"]


def apply_type(i: int) -> None:
    """Fyller i massa, area och Cd från katalogen när användaren byter typ."""
    sat_type = SATELLITE_TYPES[st.session_state[f"type_{i}"]]
    st.session_state[f"mass_{i}"] = sat_type.mass
    st.session_state[f"area_{i}"] = sat_type.area
    st.session_state[f"cd_{i}"] = sat_type.drag_coefficient


def satellite_inputs(i: int) -> SatelliteInput:
    """Inmatning för satellit nummer i, i en egen utfällbar ruta."""
    if f"type_{i}" not in st.session_state:                 # första gången: förifyll från katalogen
        st.session_state[f"type_{i}"] = DEFAULT_TYPES[i]
        apply_type(i)

    with st.expander(f"Satellite {i + 1}", expanded=(i == 0)):
        name = st.text_input("Name", value=f"Sat {i + 1}", key=f"name_{i}")
        type_name = st.selectbox("Type", list(SATELLITE_TYPES), key=f"type_{i}", on_change=apply_type, args=(i,))
        st.caption(SATELLITE_TYPES[type_name].description)
        c1, c2 = st.columns(2)
        mass = c1.number_input("Mass [kg]", min_value=0.5, max_value=1000.0, step=1.0, key=f"mass_{i}")
        area = c2.number_input("Area [m²]", min_value=0.005, max_value=20.0, step=0.01, format="%.3f", key=f"area_{i}")
        c3, c4 = st.columns(2)
        cd = c3.number_input("Cd [-]", min_value=1.0, max_value=4.0, step=0.1, key=f"cd_{i}")
        speed = c4.number_input("Separation speed [m/s]", min_value=0.1, max_value=3.0, value=1.0, step=0.1, key=f"speed_{i}")
    return SatelliteInput(name, mass, area, cd, speed)


# --- Sidopanel: uppdragets förutsättningar ---
with st.sidebar:
    st.header("Orbit")
    altitude_km = st.slider("Altitude [km]", 400, 600, 500, step=10,
                            help="The atmosphere model is built around 500 km and is reasonable between 400 and 600 km.")
    inclination = st.number_input("Inclination [°]", 0.0, 180.0, 97.4, step=0.1,
                                  help="97.4° gives a sun-synchronous orbit at 500 km.")

    st.header("Upper stage")
    stage_mass = st.number_input("Mass without satellites [kg]", 100.0, 10000.0, 1200.0, step=50.0)
    stage_area = st.number_input("Area [m²]", 0.5, 50.0, 10.0, step=0.5)

    st.header("Satellites")
    n_sats = st.slider("Number of satellites", 2, 5, 3, help="Satellites are released in the order listed here.")
    sat_inputs = [satellite_inputs(i) for i in range(n_sats)]

mission = mission_from_inputs(altitude_km, inclination, stage_mass, stage_area, sat_inputs)

# --- Huvudyta ---
st.title("🛰️ Satellite separation planner")
st.write(
    "Define the orbit, the upper stage and the satellites in the panel on the left. "
    "The optimizer then chooses the direction and timing of each separation so that "
    "no objects come too close to each other – during the first orbits and for a week afterwards."
)

st.subheader("Mission")
summary = pd.DataFrame(
    [
        {
            "Satellite": s.name,
            "Mass [kg]": s.mass,
            "Area [m²]": s.area,
            "Area/mass [m²/kg]": s.area / s.mass,
            "Separation speed [m/s]": s.spring_impulse / s.mass,
            "Spring impulse [N·s]": s.spring_impulse,
        }
        for s in mission.satellites
    ]
)
st.dataframe(summary, hide_index=True, use_container_width=True,
             column_config={"Area/mass [m²/kg]": st.column_config.NumberColumn(format="%.4f")})

total_sat_mass = sum(s.mass for s in mission.satellites)
c1, c2, c3 = st.columns(3)
c1.metric("Total satellite mass", f"{total_sat_mass:.0f} kg")
c2.metric("Stack mass at start", f"{mission.stage_mass + total_sat_mass:.0f} kg")
c3.metric("Altitude", f"{altitude_km} km")

ratios = [s.area / s.mass for s in mission.satellites]
if max(ratios) / min(ratios) > 5:
    st.info(
        "The satellites have very different area-to-mass ratios. Drag brakes them by "
        "different amounts, so close passes can occur days after separation – this is "
        "where the numerical check makes a difference."
    )

st.button("Optimize separation plan", type="primary", disabled=True, help="Coming in the next step.")