"""Rymdbakgrund för Streamlit-appen: blinkande stjärnor, nebulosor och stjärnfall.

Allt är ren CSS som läggs in på sidan med st.markdown. Stjärnorna är inga bilder:
varje stjärngrupp är en enda pixel-stor <div> vars `box-shadow` har hundratals
skuggor, en per stjärna, utspridda över skärmen. Grupperna blinkar i olika takt,
så att himlen ser levande ut utan att någon JavaScript behövs.
"""

import random

import matplotlib.pyplot as plt
import streamlit as st

# Stjärnornas färger: de flesta vitaktiga, några blå (heta) och gula/orange (svalare)
STAR_COLORS = ["#ffffff"] * 6 + ["#cfe0ff", "#aac8ff", "#fff4d6", "#ffd9a8"]


def _star_shadows(rng: random.Random, n: int, size: float, alpha: tuple[float, float]) -> str:
    """En box-shadow-lista med n stjärnor på slumpade platser (i vw/vh, så de täcker hela fönstret)."""
    shadows = []
    for _ in range(n):
        color = rng.choice(STAR_COLORS)
        opacity = rng.uniform(*alpha)
        r, g, b = (int(color[k:k + 2], 16) for k in (1, 3, 5))
        shadows.append(f"{rng.uniform(0, 100):.2f}vw {rng.uniform(0, 100):.2f}vh 0 {size / 2:g}px "
                       f"rgba({r},{g},{b},{opacity:.2f})")
    return ", ".join(shadows)


def _star_layers(rng: random.Random) -> tuple[str, str]:
    """HTML och CSS för stjärnlagren. Varje grupp får egen blinkperiod och fördröjning."""
    html, css = [], []
    layers = [  # (antal grupper, stjärnor per grupp, storlek [px], ljusstyrka)
        (6, 90, 1.0, (0.35, 0.8)),     # många små, svaga stjärnor
        (5, 35, 1.6, (0.6, 0.95)),     # medelstora
        (3, 12, 2.4, (0.85, 1.0)),     # få, stora och klara
    ]
    k = 0
    for n_groups, n_stars, size, alpha in layers:
        for _ in range(n_groups):
            period = rng.uniform(2.5, 7.0)
            delay = rng.uniform(0, period)
            css.append(
                f".sp-stars-{k} {{ width:1px; height:1px; box-shadow:{_star_shadows(rng, n_stars, size, alpha)};"
                f" animation: sp-twinkle {period:.2f}s ease-in-out {-delay:.2f}s infinite; }}"
            )
            html.append(f'<div class="sp-stars sp-stars-{k}"></div>')
            k += 1
    return "".join(html), "\n".join(css)


def _bright_stars(rng: random.Random, n: int = 14) -> tuple[str, str]:
    """Några riktigt klara stjärnor med strålkors (som på teleskopbilder)."""
    html = []
    for _ in range(n):
        period = rng.uniform(3.0, 8.0)
        html.append(
            f'<div class="sp-bright" style="left:{rng.uniform(2, 98):.1f}vw; top:{rng.uniform(2, 98):.1f}vh; '
            f'--s:{rng.uniform(0.6, 1.3):.2f}; animation-duration:{period:.1f}s; '
            f'animation-delay:{-rng.uniform(0, period):.1f}s"></div>'
        )
    return "".join(html), ""


CSS = """
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&display=swap');

/* --- Gör Streamlits egna lager genomskinliga så att rymden syns bakom --- */
html { background: #03040b; }
body {
    background:
        radial-gradient(ellipse at 20% 0%, #0d1233 0%, transparent 55%),
        radial-gradient(ellipse at 80% 100%, #120a26 0%, transparent 60%),
        #03040b !important;
    background-attachment: fixed !important;
}
[data-testid="stApp"], [data-testid="stAppViewContainer"], [data-testid="stMain"], [data-testid="stHeader"],
[data-testid="stBottomBlockContainer"] { background: transparent !important; }

/* Sidopanelen som en halvgenomskinlig glasruta */
[data-testid="stSidebar"] {
    background: rgba(8, 11, 28, 0.72) !important;
    backdrop-filter: blur(10px);
    border-right: 1px solid rgba(140, 160, 255, 0.12);
}

/* Rubriker i ett "rymdigare" typsnitt, titeln med en svag glödande gradient */
h1, h2, h3 { font-family: 'Space Grotesk', sans-serif !important; letter-spacing: 0.01em; }
.sp-title {
    background: linear-gradient(90deg, #e8ecff 0%, #9fb4ff 45%, #d39bff 100%);
    -webkit-background-clip: text; background-clip: text; color: transparent !important;
    filter: drop-shadow(0 0 18px rgba(140, 150, 255, 0.35));
}

/* Tabeller, nyckeltal och flikar på mörka glasrutor så att texten går att läsa */
[data-testid="stDataFrame"], [data-testid="stMetric"], [data-testid="stExpander"] details,
[data-testid="stTabs"] [role="tabpanel"], [data-testid="stImage"], [data-testid="stAlert"] {
    background: rgba(8, 12, 30, 0.62);
    border-radius: 10px;
    backdrop-filter: blur(6px);
}
[data-testid="stMetric"] { padding: 0.7rem 1rem; border: 1px solid rgba(140, 160, 255, 0.14); }

/* --- Bakgrunden --- */
.sp-space { position: fixed; inset: 0; z-index: -1; pointer-events: none; overflow: hidden; }
.sp-stars { position: absolute; top: 0; left: 0; border-radius: 50%; }

@keyframes sp-twinkle {
    0%, 100% { opacity: 1; }
    50%      { opacity: 0.25; }
}

/* Klara stjärnor med strålkors */
.sp-bright {
    position: absolute; width: 3px; height: 3px; border-radius: 50%;
    background: #fff; transform: scale(var(--s));
    box-shadow: 0 0 6px 2px rgba(200, 220, 255, 0.9), 0 0 14px 4px rgba(150, 180, 255, 0.35);
    animation-name: sp-glint; animation-timing-function: ease-in-out; animation-iteration-count: infinite;
}
.sp-bright::before, .sp-bright::after {
    content: ""; position: absolute; left: 50%; top: 50%;
    background: linear-gradient(90deg, transparent, rgba(220, 230, 255, 0.85), transparent);
    transform: translate(-50%, -50%);
}
.sp-bright::before { width: 26px; height: 1px; }
.sp-bright::after  { width: 1px; height: 26px;
    background: linear-gradient(0deg, transparent, rgba(220, 230, 255, 0.85), transparent); }
@keyframes sp-glint {
    0%, 100% { opacity: 1;    transform: scale(var(--s)); }
    50%      { opacity: 0.45; transform: scale(calc(var(--s) * 0.7)); }
}

/* Nebulosor: stora, suddiga färgmoln som sakta glider och andas */
.sp-nebula { position: absolute; border-radius: 50%; filter: blur(60px); mix-blend-mode: screen;
             animation: sp-drift ease-in-out infinite alternate; }
.sp-nebula.n1 { width: 60vw; height: 45vh; left: 18vw; top: 10vh;
    background: radial-gradient(ellipse, rgba(120, 60, 200, 0.40) 0%, rgba(70, 30, 140, 0.18) 45%, transparent 70%);
    animation-duration: 70s; }
.sp-nebula.n2 { width: 50vw; height: 50vh; right: -10vw; top: -12vh;
    background: radial-gradient(ellipse, rgba(30, 140, 180, 0.45) 0%, rgba(20, 80, 140, 0.2) 50%, transparent 72%);
    animation-duration: 90s; animation-delay: -30s; }
.sp-nebula.n3 { width: 45vw; height: 40vh; right: 5vw; bottom: -10vh;
    background: radial-gradient(ellipse, rgba(210, 60, 130, 0.38) 0%, rgba(120, 30, 90, 0.16) 50%, transparent 72%);
    animation-duration: 80s; animation-delay: -55s; }
.sp-nebula.n4 { width: 30vw; height: 28vh; left: 30vw; top: 55vh;
    background: radial-gradient(ellipse, rgba(60, 90, 220, 0.30) 0%, transparent 70%);
    animation-duration: 60s; animation-delay: -12s; }
@keyframes sp-drift {
    from { transform: translate(0, 0) scale(1) rotate(0deg); opacity: 0.85; }
    to   { transform: translate(4vw, 3vh) scale(1.12) rotate(6deg); opacity: 1; }
}

/* Vintergatan: ett svagt, diagonalt ljusband */
.sp-milkyway { position: absolute; left: -20vw; top: 35vh; width: 140vw; height: 22vh;
    transform: rotate(-18deg); filter: blur(30px);
    background: radial-gradient(ellipse at center, rgba(190, 200, 255, 0.10) 0%, rgba(160, 140, 220, 0.05) 45%,
                transparent 70%); }

/* Stjärnfall: syns bara en kort stund av varje period */
.sp-meteor { position: absolute; width: 140px; height: 1.5px; opacity: 0;
    background: linear-gradient(90deg, rgba(255,255,255,0.95), rgba(170,200,255,0.4) 40%, transparent);
    transform: rotate(-35deg); transform-origin: left center;
    animation: sp-meteor linear infinite; }
.sp-meteor.m1 { top: 12vh; left: 78vw; animation-duration: 11s; animation-delay: 3s; }
.sp-meteor.m2 { top: 30vh; left: 55vw; animation-duration: 17s; animation-delay: 9s; }
.sp-meteor.m3 { top: 6vh;  left: 35vw; animation-duration: 23s; animation-delay: 15s; }
@keyframes sp-meteor {
    0%   { opacity: 0; transform: rotate(-35deg) translateX(0); }
    1%   { opacity: 1; }
    6%   { opacity: 0; transform: rotate(-35deg) translateX(-38vw); }
    100% { opacity: 0; transform: rotate(-35deg) translateX(-38vw); }
}

/* Den som har valt "minska rörelse" i operativsystemet får en stillastående himmel */
@media (prefers-reduced-motion: reduce) {
    .sp-stars, .sp-bright, .sp-nebula, .sp-meteor { animation: none !important; }
}
"""


def apply_matplotlib_theme() -> None:
    """Mörka grafer som smälter in i bakgrunden."""
    plt.style.use("dark_background")
    plt.rcParams.update({
        "figure.facecolor": (0.03, 0.05, 0.12, 0.9),
        "axes.facecolor": (0.03, 0.05, 0.12, 0.0),
        "savefig.facecolor": (0.03, 0.05, 0.12, 0.9),
        "axes.edgecolor": "#5a6690",
        "grid.color": "#8090c0",
        "legend.facecolor": (0.05, 0.07, 0.16, 0.85),
        "legend.edgecolor": "#3a4570",
        "axes.prop_cycle": plt.cycler(color=["#7aa2ff", "#ff8fb3", "#7fe0c8", "#ffd27a",
                                             "#c59bff", "#ff9f6e", "#9be27a", "#6fd3ff"]),
    })


def apply_space_theme(seed: int = 7) -> None:
    """Lägger rymdbakgrunden på sidan. Anropas en gång, direkt efter st.set_page_config."""
    rng = random.Random(seed)            # samma himmel varje gång sidan ritas om
    stars_html, stars_css = _star_layers(rng)
    bright_html, _ = _bright_stars(rng)
    html = (
        '<div class="sp-space">'
        '<div class="sp-milkyway"></div>'
        '<div class="sp-nebula n1"></div><div class="sp-nebula n2"></div>'
        '<div class="sp-nebula n3"></div><div class="sp-nebula n4"></div>'
        f"{stars_html}{bright_html}"
        '<div class="sp-meteor m1"></div><div class="sp-meteor m2"></div><div class="sp-meteor m3"></div>'
        "</div>"
    )
    # Tomma rader skulle avsluta HTML-blocket i Markdown, så de tas bort
    css = "\n".join(line for line in f"{CSS}\n{stars_css}".splitlines() if line.strip())
    st.markdown(f"<style>{css}</style>{html}", unsafe_allow_html=True)
    apply_matplotlib_theme()