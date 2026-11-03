from streamlit.testing.v1 import AppTest

APP = "../app/streamlit_app.py"    # sökvägen räknas från testfilens mapp


def test_app_starts_without_errors():
    at = AppTest.from_file(APP, default_timeout=30).run()
    assert not at.exception
    assert len(at.dataframe) == 1


def test_changing_satellite_type_fills_in_catalog_values():
    at = AppTest.from_file(APP, default_timeout=30).run()
    at.selectbox(key="type_0").set_value("3U CubeSat").run()
    assert at.number_input(key="mass_0").value == 4.0
    assert at.number_input(key="area_0").value == 0.03


def test_number_of_satellites_can_change():
    at = AppTest.from_file(APP, default_timeout=30).run()
    at.slider[1].set_value(5).run()                       # andra reglaget = antal satelliter
    assert not at.exception
    assert len(at.dataframe[0].value) == 5