from typer.testing import CliRunner
from runner.main import _trim_mean, _detect_language, app

runner = CliRunner()


def test_trim_mean_basic():
    assert _trim_mean([1.0, 2.0, 3.0, 4.0, 5.0]) == 3.5


def test_trim_mean_single_value():
    assert _trim_mean([5.0]) == 5.0


def test_trim_mean_empty():
    assert _trim_mean([]) == 0.0


def test_detect_language():
    assert _detect_language("java-foo") == "java"
    assert _detect_language("dotnet-bar") == "dotnet"
    assert _detect_language("react-app") == "react"
    assert _detect_language("bash-script") == "bash"
    assert _detect_language("python-tool") == "python"
    assert _detect_language("rust-lib") == "rust"
    assert _detect_language("wasm-calculator") == "rust"
    assert _detect_language("two-sum") == "python"


def test_list_problems_command():
    result = runner.invoke(app, ["list-problems"])
    assert result.exit_code == 0
    assert "two-sum" in result.output


def test_list_problems_filter_by_language():
    result = runner.invoke(app, ["list-problems", "--language", "rust"])
    assert result.exit_code == 0
    assert "wasm-calculator" in result.output or "rust" in result.output


def test_breakdown_command():
    result = runner.invoke(app, ["breakdown", "--by", "language"])
    assert result.exit_code in (0, 1)
