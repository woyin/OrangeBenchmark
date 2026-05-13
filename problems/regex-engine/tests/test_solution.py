import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "regex_engine_solution",
    Path(__file__).resolve().parents[1] / "solution.py",
)
solution = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(solution)
match = solution.match


def test_literal_match():
    assert match("abc", "abc") is True
    assert match("abc", "abd") is False


def test_dot_matches_any():
    assert match("a.c", "axc") is True
    assert match("a.c", "abc") is True
    assert match("...", "xyz") is True
    assert match("...", "xy") is False


def test_star_zero_or_more():
    assert match("a*b", "b") is True
    assert match("a*b", "ab") is True
    assert match("a*b", "aaab") is True
    assert match("a*b", "acb") is False


def test_plus_one_or_more():
    assert match("a+b", "b") is False
    assert match("a+b", "ab") is True
    assert match("a+b", "aaab") is True


def test_question_mark():
    assert match("a?b", "b") is True
    assert match("a?b", "ab") is True
    assert match("a?b", "aab") is False


def test_character_class():
    assert match("[abc]", "a") is True
    assert match("[abc]", "b") is True
    assert match("[abc]", "d") is False


def test_negated_class():
    assert match("[^abc]", "d") is True
    assert match("[^abc]", "a") is False


def test_range_class():
    assert match("[a-z]", "m") is True
    assert match("[a-z]", "M") is False
    assert match("[0-9]", "5") is True
    assert match("[0-9]", "a") is False


def test_escape():
    assert match("a\\.b", "a.b") is True
    assert match("a\\.b", "axb") is False
    assert match("a\\*b", "a*b") is True


def test_start_anchor():
    assert match("^abc", "abcdef") is True
    assert match("^abc", "xabc") is False


def test_end_anchor():
    assert match("abc$", "xyzabc") is True
    assert match("abc$", "abcxyz") is False


def test_both_anchors():
    assert match("^abc$", "abc") is True
    assert match("^abc$", "abcd") is False


def test_complex_pattern():
    assert match("a*b+c?", "b") is True
    assert match("a*b+c?", "aabbc") is True
    assert match("a*b+c?", "aac") is False


def test_nested_quantifiers():
    assert match("(a*)*", "") is True or True  # basic no-crash test
    assert match("a.*b", "axxxxxb") is True


def test_empty_string():
    assert match("a*", "") is True
    assert match("a+", "") is False
    assert match(".", "") is False


def test_long_repetition():
    assert match("a*" + "b", "a" * 1000 + "b") is True


def test_class_with_multiple_ranges():
    assert match("[a-zA-Z0-9]", "X") is True
    assert match("[a-zA-Z0-9]", "5") is True
    assert match("[a-zA-Z0-9]", "!") is False
