import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "metar_solution",
    Path(__file__).resolve().parents[1] / "solution.py",
)
solution = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(solution)
parse_metar = solution.parse_metar


def test_standard_metar():
    result = parse_metar("KJFK 121851Z 27010KT 10SM FEW060 SCT100 22/12 A3012 RMK AO2")
    assert result["station"] == "KJFK"
    assert result["time"]["day"] == 12
    assert result["time"]["hour"] == 18
    assert result["time"]["minute"] == 51
    assert result["wind"]["direction"] == 270
    assert result["wind"]["speed"] == 10
    assert result["wind"]["gust"] is None
    assert result["visibility"] == "10SM"
    assert len(result["clouds"]) == 2
    assert result["clouds"][0] == {"sky_cover": "FEW", "altitude": 60}
    assert result["temperature"] == 22
    assert result["dewpoint"] == 12
    assert result["altimeter"] == 30.12
    assert "AO2" in result["remarks"]


def test_metar_with_gusts():
    result = parse_metar("KLAX 010000Z 27010G25KT 9999 FEW060 18/08 A2992")
    assert result["wind"]["gust"] == 25
    assert result["visibility"] == 9999
    assert result["auto"] is False


def test_auto_station():
    result = parse_metar("KJFK 121851Z AUTO 27010KT 10SM OVC080 22/12 A3012")
    assert result["auto"] is True


def test_variable_wind():
    result = parse_metar("KJFK 121851Z VRB05KT 10SM SKC 30/15 A3010")
    assert result["wind"]["direction"] == "VRB"
    assert result["wind"]["speed"] == 5


def test_negative_temperature():
    result = parse_metar("KJFK 121851Z 27010KT 10SM SKC M05/M10 A3010")
    assert result["temperature"] == -5
    assert result["dewpoint"] == -10


def test_sky_clear():
    result = parse_metar("KJFK 121851Z 27010KT 10SM SKC 25/15 A3015")
    assert result["clouds"] == [{"sky_cover": "SKC", "altitude": None}]


def test_multiple_cloud_layers():
    result = parse_metar("KJFK 121851Z 27010KT 5SM FEW010 SCT030 BKN060 OVC100 20/10 A2990")
    assert len(result["clouds"]) == 4


def test_no_remarks():
    result = parse_metar("KJFK 121851Z 27010KT 10SM SKC 25/15 A3015")
    assert result["remarks"] == ""


def test_fractional_visibility():
    result = parse_metar("KJFK 121851Z 27010KT 1/2SM FEW060 22/12 A3012")
    assert result["visibility"] == "1/2SM"
