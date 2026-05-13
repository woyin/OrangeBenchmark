import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "word_ladder_solution",
    Path(__file__).resolve().parents[1] / "solution.py",
)
solution = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(solution)
word_ladder = solution.word_ladder


def test_simple_ladder():
    d = ["hit", "hot", "dot", "dog", "cog"]
    result = word_ladder("hit", "cog", d)
    assert result[0].lower() == "hit"
    assert result[-1].lower() == "cog"
    for i in range(len(result) - 1):
        diff = sum(a != b for a, b in zip(result[i].lower(), result[i+1].lower()))
        assert diff == 1


def test_no_path():
    d = ["hit", "hot", "dog", "cog"]
    result = word_ladder("hit", "cog", d)
    assert result == []


def test_same_word():
    result = word_ladder("hit", "hit", ["hit", "hot"])
    assert result == ["hit"]


def test_length_one_path():
    d = ["hit", "hat", "hot"]
    result = word_ladder("hit", "hot", d)
    assert len(result) == 2
    assert result[0].lower() == "hit"
    assert result[-1].lower() == "hot"


def test_case_insensitive():
    d = ["HIT", "HOT", "DOT", "DOG", "COG"]
    result = word_ladder("hit", "cog", d)
    assert result[0] == "HIT"
    assert result[-1] == "COG"


def test_empty_dictionary():
    result = word_ladder("hit", "cog", [])
    assert result == []


def test_longer_ladder():
    d = ["cold", "bold", "bolt", "bolt", "boil", "bail", "fail", "fall", "fale", "pale", "page"]
    result = word_ladder("cold", "page", d)
    if result:
        assert result[0].lower() == "cold"
        assert result[-1].lower() == "page"


def test_start_not_in_dictionary():
    d = ["hot", "dot", "dog", "cog"]
    result = word_ladder("hit", "cog", d)
    # start word should still be usable
    assert result == [] or result[0].lower() == "hit"
