"""Tests for merge_sort."""

from solution import merge_sort


def test_empty():
    assert merge_sort([]) == []


def test_single():
    assert merge_sort([1]) == [1]


def test_sorted():
    assert merge_sort([1, 2, 3]) == [1, 2, 3]


def test_reverse():
    assert merge_sort([3, 2, 1]) == [1, 2, 3]


def test_duplicates():
    assert merge_sort([3, 1, 2, 1, 3]) == [1, 1, 2, 3, 3]


def test_negative():
    assert merge_sort([-1, 3, -2, 0]) == [-2, -1, 0, 3]


def test_large():
    import random
    arr = list(range(100))
    random.shuffle(arr)
    assert merge_sort(arr) == list(range(100))
