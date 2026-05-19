import tempfile
from pathlib import Path

from runner.scorer import (
    _continuous_performance_score,
    _type_hint_score,
    _complexity_score,
    _docstring_score,
    _error_handling_score,
    _security_score,
    _robustness_score,
    _resource_efficiency_score,
)


def test_continuous_performance_fast_boundary():
    assert _continuous_performance_score(0.5, fast=1.0, slow=10.0) == 1.0


def test_continuous_performance_slow_boundary():
    assert _continuous_performance_score(15.0, fast=1.0, slow=10.0) == 0.0


def test_continuous_performance_midpoint():
    # t=0.5, (1-0.5)^2 = 0.25
    assert _continuous_performance_score(5.5, fast=1.0, slow=10.0) == 0.25


def test_continuous_performance_not_ok():
    assert _continuous_performance_score(0.5, fast=1.0, slow=10.0, ok=False) == 0.0


def test_type_hint_score_full_coverage():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("""
def add(a: int, b: int) -> int:
    return a + b

def greet(name: str) -> str:
    return f"Hello {name}"
""")
        f.flush()
        path = Path(f.name)
    score = _type_hint_score(path)
    assert score == 1.0


def test_type_hint_score_partial():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("""
def add(a, b: int):
    return a + b
""")
        f.flush()
        path = Path(f.name)
    score = _type_hint_score(path)
    assert 0.0 < score < 1.0


def test_complexity_score_simple():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("""
def simple(x):
    if x > 0:
        return x
    return 0
""")
        f.flush()
        path = Path(f.name)
    score = _complexity_score(path)
    # one if -> cc=2, avg_cc=2, 1.0 - (2-1)*0.1 = 0.9
    assert score == 0.9


def test_docstring_score_full():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write('"""Module doc."""\ndef foo():\n    """Doc."""\n    pass\n')
        f.flush()
        path = Path(f.name)
    score = _docstring_score(path)
    assert score == 1.0


def test_error_handling_score_with_try():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("""
def foo(x):
    try:
        return int(x)
    except ValueError:
        return 0
""")
        f.flush()
        path = Path(f.name)
    score = _error_handling_score(path)
    assert score == 1.0


def test_security_score_clean():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("x = 1 + 2\n")
        f.flush()
        path = Path(f.name)
    assert _security_score(path) == 1.0


def test_security_score_with_eval():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("result = eval(user_input)\n")
        f.flush()
        path = Path(f.name)
    assert _security_score(path) < 1.0


def test_robustness_score_full():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("""
def process(data):
    if not data:
        return []
    if isinstance(data, list):
        return data
    try:
        return [data]
    except Exception:
        return []
""")
        f.flush()
        path = Path(f.name)
    score = _robustness_score(path)
    # +0.25 empty input, +0.25 exception type, +0.0 boundary, +0.25 validation = 0.75
    assert score == 0.75


def test_resource_efficiency_score_unclosed_file():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("f = open('file.txt')\n")
        f.flush()
        path = Path(f.name)
    score = _resource_efficiency_score(path)
    assert score < 1.0
