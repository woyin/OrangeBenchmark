import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "two_sum_solution",
    Path(__file__).resolve().parents[1] / "solution.py",
)
solution = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(solution)
two_sum = solution.two_sum


def assert_pair(nums: list[int], target: int, result: list[int]):
    assert len(result) == 2
    i, j = result
    assert i != j
    assert nums[i] + nums[j] == target


def test_basic_pair():
    assert two_sum([2, 7, 11, 15], 9) == [0, 1]


def test_duplicates():
    assert two_sum([3, 3], 6) == [0, 1]


def test_negative_numbers():
    assert two_sum([-1, -2, -3, -4, -5], -8) == [2, 4]


def test_no_solution_returns_empty_list():
    assert two_sum([1, 2, 3], 99) == []


def test_empty_and_single_item():
    assert two_sum([], 1) == []
    assert two_sum([1], 1) == []


def test_zero_sum_pair():
    nums = [10, -5, 3, 5]
    assert_pair(nums, 0, two_sum(nums, 0))


def test_large_input():
    nums = list(range(100_000))
    result = two_sum(nums, 199_997)
    assert_pair(nums, 199_997, result)


def test_all_same_elements():
    nums = [5] * 100
    assert_pair(nums, 10, two_sum(nums, 10))


def test_multiple_valid_pairs():
    nums = [1, 2, 3, 4, 5]
    result = two_sum(nums, 6)
    assert_pair(nums, 6, result)


def test_target_is_zero_with_zeros():
    assert_pair([0, 1, 0], 0, two_sum([0, 1, 0], 0))


def test_two_element_no_solution():
    assert two_sum([1, 2], 5) == []


def test_very_large_numbers():
    big = 10**18
    assert_pair([big, big - 1, 1], big, two_sum([big, big - 1, 1], big))
