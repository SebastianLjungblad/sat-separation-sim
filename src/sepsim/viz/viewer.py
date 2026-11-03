"""3D-visaren: bygger en fristående HTML-fil av exportdata från sepsim.export.

HTML-filen innehåller all banedata. Three.js, jordens texturer och stjärnkatalogen
laddas från ett CDN när sidan öppnas, så filen fungerar i alla webbläsare med internet.
"""

import json
from importlib.resources import files
from pathlib import Path

PLACEHOLDER = "/*__SEPSIM_DATA__*/null"


def viewer_html(data: dict) -> str:
    """HTML-sidan med datan inbakad."""
    template = (files("sepsim.viz") / "viewer.html").read_text(encoding="utf-8")
    payload = json.dumps(data, separators=(",", ":")).replace("</", "<\\/")   # får inte avsluta <script>
    return template.replace(PLACEHOLDER, payload)


def write_viewer(data: dict, path: str | Path) -> Path:
    """Sparar visaren som en HTML-fil som kan öppnas direkt i webbläsaren."""
    path = Path(path)
    path.write_text(viewer_html(data), encoding="utf-8")
    return path