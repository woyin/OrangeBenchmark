from runner.main import _trim_mean, _detect_language


def test_trim_mean_basic():
    # [1,2,3,4,5] sorted -> remove bottom 10% (1 item) -> [2,3,4,5] avg = 3.5
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
