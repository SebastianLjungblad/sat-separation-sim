"""Tester för 3D-visarens HTML-sida."""

import json

from sepsim.export import export_trajectories
from sepsim.scenario import load_mission
from sepsim.viz.viewer import PLACEHOLDER, viewer_html


def test_viewer_contains_data_and_no_placeholder():
    data = export_trajectories(load_mission("scenarios/scenario1.toml"), days=0.05)
    html = viewer_html(data)
    assert PLACEHOLDER not in html
    assert '"format":"sepsim-trajectories/1"' in html
    assert html.count("<script") == html.count("</script>")


def test_names_cannot_close_the_script_tag():
    data = {"name": "</script><script>alert(1)</script>"}
    html = viewer_html(data)
    payload = html.split("const DATA = ")[1].split(";\n")[0]
    assert "</script>" not in payload
    assert json.loads(payload) == data