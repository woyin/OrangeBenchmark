import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "url_parser_solution",
    Path(__file__).resolve().parents[1] / "solution.py",
)
solution = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(solution)
parse_url = solution.parse_url


def test_full_url():
    assert parse_url("https://example.com:8080/path?key=value&foo=bar#section") == {
        "scheme": "https",
        "host": "example.com",
        "port": 8080,
        "path": "/path",
        "query_params": {"key": "value", "foo": "bar"},
        "fragment": "section",
    }


def test_missing_scheme():
    assert parse_url("example.com/path")["scheme"] is None


def test_default_ports():
    assert parse_url("http://host/path")["port"] == 80
    assert parse_url("https://host/path")["port"] == 443


def test_no_path():
    parsed = parse_url("https://example.com")
    assert parsed["path"] == ""
    assert parsed["query_params"] == {}


def test_query_percent_decoding():
    parsed = parse_url("https://host/search?q=%E4%B8%AD%E6%96%87&space=a+b")
    assert parsed["query_params"] == {"q": "中文", "space": "a b"}


def test_empty_url():
    assert parse_url("") == {
        "scheme": None,
        "host": None,
        "port": None,
        "path": "",
        "query_params": {},
        "fragment": None,
    }


def test_path_only_url():
    assert parse_url("/foo/bar") == {
        "scheme": None,
        "host": None,
        "port": None,
        "path": "/foo/bar",
        "query_params": {},
        "fragment": None,
    }


def test_empty_fragment():
    assert parse_url("https://host/path#")["fragment"] == ""
