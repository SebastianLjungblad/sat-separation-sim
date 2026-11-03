"""sepsim – satellite separation planner (Streamlit app).

Starta med:
    uv run streamlit run app/streamlit_app.py

All kod som ritar gränssnittet ligger i main(), som bara körs när filen startas
av Streamlit. Det behövs eftersom den numeriska kontrollen körs i flera
processer samtidigt: varje ny process läser in den här filen, och utan skyddet
`if __name__ == "__main__"` skulle varje process försöka rita upp hela appen.
"""

import time
from dataclasses import dataclass

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from sepsim.analysis.long_term import SOLAR_LEVELS, RobustRow, min_distance_over_time, rank_robust
from sepsim.analysis.mission import analyze_mission
from sepsim.catalog import SATELLITE_TYPES, SatelliteInput, mission_from_inputs
from sepsim.dynamics.forces import ForceModel
from sepsim.dynamics.separation import angles_from_direction
from sepsim.optimize import optimize_candidates
from sepsim.scenario import Mission, mission_to_toml
from sepsim.viz.plots import plot_distances, plot_min_distance_over_time, plot_trajectories
from sepsim.viz.space_theme import apply_space_theme

DEFAULT_TYPES = ["Microsat with solar panels", "6U CubeSat", "Compact smallsat", "12U CubeSat", "3U CubeSat"]


@dataclass
class Settings:
    """Optimeringens inställningar från sidopanelen."""
    n_candidates: int
    days: int
    safety: float
    clearance: float
    min_gap: float
    max_gap: float
    maxiter: int


# --- Sidopanel ---------------------------------------------------------------

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
        speed = c4.number_input("Separation speed [m/s]", min_value=0.1, max_value=3.0, value=1.0, step=0.1,
                                key=f"speed_{i}")
    return SatelliteInput(name, mass, area, cd, speed)


def sidebar() -> tuple[Mission, Settings]:
    """Hela sidopanelen: uppdragets förutsättningar och optimeringens inställningar."""
    with st.sidebar:
        st.header("Orbit")
        altitude_km = st.slider("Altitude [km]", 400, 600, 500, step=10,
                                help="The atmosphere model is built around 500 km and is reasonable "
                                     "between 400 and 600 km.")
        inclination = st.number_input("Inclination [°]", 0.0, 180.0, 97.4, step=0.1,
                                      help="97.4° gives a sun-synchronous orbit at 500 km.")

        st.header("Upper stage")
        stage_mass = st.number_input("Mass without satellites [kg]", 100.0, 10000.0, 1200.0, step=50.0)
        stage_area = st.number_input("Area [m²]", 0.5, 50.0, 10.0, step=0.5)

        st.header("Satellites")
        n_sats = st.slider("Number of satellites", 2, 5, 3, help="Satellites are released in the order listed here.")
        sat_inputs = [satellite_inputs(i) for i in range(n_sats)]

        st.header("Optimization")
        n_candidates = st.slider("Candidate plans from CW", 3, 20, 10,
                                 help="How many of the CW optimizer's best plans are checked with the numerical model.")
        days = st.slider("Numerical check [days]", 3, 21, 7,
                         help="How long each candidate is propagated with J2 and drag, at three solar activity levels.")
        safety = st.number_input("Safety distance [m]", 1.0, 1000.0, 10.0, step=5.0)
        with st.expander("Advanced"):
            clearance = st.number_input("Clearance time after each separation [s]", 60.0, 3600.0, 600.0, step=60.0)
            min_gap, max_gap = st.slider("Time between separations [s]", 10, 900, (30, 300), step=10)
            maxiter = st.slider("Optimizer generations", 5, 300, 150, step=5,
                                help="More generations give a more thorough search but take longer.")

    mission = mission_from_inputs(altitude_km, inclination, stage_mass, stage_area, sat_inputs)
    settings = Settings(n_candidates, days, safety, clearance, float(min_gap), float(max_gap), maxiter)
    return mission, settings


# --- Uppdraget -------------------------------------------------------------

def show_mission(mission: Mission) -> None:
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
    c3.metric("Altitude", f"{mission.altitude / 1000:.0f} km")

    ratios = [s.area / s.mass for s in mission.satellites]
    if max(ratios) / min(ratios) > 5:
        st.info(
            "The satellites have very different area-to-mass ratios. Drag brakes them by "
            "different amounts, so close passes can occur days after separation – this is "
            "where the numerical check makes a difference."
        )


# --- Optimering --------------------------------------------------------------

def run_optimization(mission: Mission, settings: Settings, run_key: str) -> None:
    """Tvåstegsoptimeringen med förloppsindikator. Resultatet sparas i session_state."""
    progress = st.progress(0.0, text="Step 1/2: CW optimizer searching for candidate plans…")
    start = time.time()

    def cw_progress(generation: int, max_generations: int, best: float) -> None:
        progress.progress(0.5 * generation / max_generations,
                          text=f"Step 1/2: CW optimizer, generation {generation}/{max_generations} "
                               f"– best minimum distance {best:.0f} m")

    candidates = optimize_candidates(
        mission, n_candidates=settings.n_candidates, min_gap=settings.min_gap, max_gap=settings.max_gap,
        clearance=settings.clearance, maxiter=settings.maxiter, progress=cw_progress,
    )
    cw_time = time.time() - start

    def numerical_progress(done: int, total: int) -> None:
        progress.progress(0.5 + 0.5 * done / total,
                          text=f"Step 2/2: numerical check, {done}/{total} runs of {settings.days} days "
                               "(J2 + drag, three solar activity levels)")

    start = time.time()
    rows = rank_robust(candidates, days=settings.days, progress=numerical_progress)
    progress.empty()

    st.session_state["result"] = dict(key=run_key, rows=rows, settings=settings,
                                      cw_time=cw_time, num_time=time.time() - start)


# --- Resultat --------------------------------------------------------------

def show_candidates(rows: list[RobustRow], cw_favourite: RobustRow, settings: Settings,
                    cw_time: float, num_time: float, safety: float) -> int:
    """Tabellen med kandidatplaner. Returnerar index för den plan användaren har valt."""
    st.subheader("Candidate plans")
    st.caption(
        f"{len(rows)} candidates from the CW optimizer ({cw_time:.0f} s), each propagated numerically for "
        f"{settings.days} days at low, medium and high solar activity "
        f"({len(rows) * len(SOLAR_LEVELS)} runs, {num_time:.0f} s). "
        "Sorted by worst case – the smallest distance between any pair over all solar activity levels."
    )
    table = pd.DataFrame(
        [
            {
                "Rank": k + 1,
                "Label": "★ Robust choice" if k == 0 else ("CW favourite" if row is cw_favourite else ""),
                "CW score [m]": row.cw_score,
                **{f"{level.capitalize()} [m]": row.results[level].min_distance for level in SOLAR_LEVELS},
                "Worst case [m]": row.worst_case,
                "Closest pair (medium)": row.results["medium"].worst_pair,
                "When [days]": row.results["medium"].time_days,
                "Status": "OK" if row.worst_case >= safety else "RISK",
            }
            for k, row in enumerate(rows)
        ]
    )
    distance_columns = ["CW score [m]", "Low [m]", "Medium [m]", "High [m]", "Worst case [m]"]
    selection = st.dataframe(
        table, hide_index=True, use_container_width=True, on_select="rerun", selection_mode="single-row",
        key="candidates_table",
        column_config={c: st.column_config.NumberColumn(format="%.0f") for c in distance_columns}
        | {"When [days]": st.column_config.NumberColumn(format="%.1f"),
           "Label": st.column_config.TextColumn(width="medium")},
    )
    selected = selection.selection.rows
    return selected[0] if selected else 0


@st.cache_data(show_spinner="Simulating the first orbits…")
def first_orbits(plan: Mission, clearance: float):
    return analyze_mission(plan, clearance=clearance)


@st.cache_data(show_spinner="Propagating the plan with J2 and drag…")
def long_term_curves(plan: Mission, days: float, clearance: float):
    curves = {}
    for level in ("medium", "high"):
        t, d = min_distance_over_time(plan, days, ForceModel(solar_activity=level), clearance=clearance)
        curves[f"{level.capitalize()} solar activity"] = d
    return t, curves


def show_plan(row: RobustRow, rank: int, cw_favourite: RobustRow, settings: Settings, safety: float) -> None:
    """Detaljvyn för en vald plan: separationerna, nyckeltal och grafer."""
    st.subheader(f"Plan #{rank}")
    st.caption("Click a row in the table above to show another plan.")

    plan = row.mission
    plan_table = pd.DataFrame(
        [
            {
                "Satellite": sat.name,
                "Released [s]": sat.t_sep,
                "Azimuth [°]": angles_from_direction(sat.direction)[0],
                "Elevation [°]": angles_from_direction(sat.direction)[1],
                "Outward [m/s]": sat.spring_impulse / sat.mass * sat.direction[0],
                "Forward [m/s]": sat.spring_impulse / sat.mass * sat.direction[1],
                "Sideways [m/s]": sat.spring_impulse / sat.mass * sat.direction[2],
            }
            for sat in plan.satellites
        ]
    )
    st.dataframe(plan_table, hide_index=True, use_container_width=True,
                 column_config={c: st.column_config.NumberColumn(format="%.2f") for c in plan_table.columns[1:]})

    c1, c2, c3 = st.columns(3)
    c1.metric("CW score (first orbits)", f"{row.cw_score:.0f} m")
    c2.metric("Worst case over the check", f"{row.worst_case:.0f} m",
              delta=f"{row.worst_case - cw_favourite.worst_case:+.0f} m vs CW favourite")
    c3.metric("Closest pair (medium)", row.results["medium"].worst_pair,
              help=f"At day {row.results['medium'].time_days:.1f}")

    st.download_button("Download plan as TOML", mission_to_toml(plan, f"Plan #{rank}"),
                       file_name=f"plan_{rank}.toml", mime="text/plain")

    tab_cw, tab_long = st.tabs(["First orbits (CW)", f"{settings.days} days (J2 + drag)"])
    with tab_cw:
        analysis = first_orbits(plan, settings.clearance)
        col1, col2 = st.columns(2)
        col1.pyplot(plot_distances(analysis.pairs, analysis.distances, analysis.t, analysis.names, safety=safety))
        col2.pyplot(plot_trajectories(analysis.positions, analysis.names))
        plt.close("all")
    with tab_long:
        t, curves = long_term_curves(plan, settings.days, settings.clearance)
        st.pyplot(plot_min_distance_over_time(t, curves, safety=safety,
                                              title="Closest distance between any pair (J2 + drag)"))
        plt.close("all")


# --- Appen -------------------------------------------------------------------

def main() -> None:
    st.set_page_config(page_title="sepsim – satellite separation planner", page_icon="🛰️", layout="wide")
    apply_space_theme()
    mission, settings = sidebar()

    st.markdown('<h1>🛰️ <span class="sp-title">Satellite separation planner</span></h1>', unsafe_allow_html=True)
    st.write(
        "Define the orbit, the upper stage and the satellites in the panel on the left. "
        "The optimizer then chooses the direction and timing of each separation so that "
        "no objects come too close to each other – during the first orbits and for days afterwards."
    )
    show_mission(mission)

    # Säkerhetsavståndet påverkar bara visningen, inte optimeringen, så det ingår inte i nyckeln
    run_key = repr(mission) + repr((settings.n_candidates, settings.days, settings.clearance,
                                    settings.min_gap, settings.max_gap, settings.maxiter))
    if st.button("Optimize separation plan", type="primary"):
        run_optimization(mission, settings, run_key)

    result = st.session_state.get("result")
    if result is None:
        return
    if result["key"] != run_key:
        st.warning("The inputs have changed since the last optimization. Run it again to update the results.")

    rows = result["rows"]
    cw_favourite = max(rows, key=lambda r: r.cw_score)
    chosen = show_candidates(rows, cw_favourite, result["settings"], result["cw_time"], result["num_time"],
                             settings.safety)
    show_plan(rows[chosen], chosen + 1, cw_favourite, result["settings"], settings.safety)


if __name__ == "__main__":
    main()