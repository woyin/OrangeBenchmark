import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "lru_cache_solution",
    Path(__file__).resolve().parents[1] / "solution.py",
)
solution = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(solution)
LRUCache = solution.LRUCache


def test_basic_eviction():
    cache = LRUCache(2)
    cache.put(1, 10)
    cache.put(2, 20)
    cache.put(3, 30)
    assert cache.get(1) == -1
    assert cache.get(2) == 20
    assert cache.get(3) == 30


def test_get_refreshes_order():
    cache = LRUCache(2)
    cache.put(1, 10)
    cache.put(2, 20)
    assert cache.get(1) == 10
    cache.put(3, 30)
    assert cache.get(2) == -1
    assert cache.get(1) == 10


def test_capacity_one():
    cache = LRUCache(1)
    cache.put(1, 10)
    cache.put(2, 20)
    assert cache.get(1) == -1
    assert cache.get(2) == 20


def test_capacity_zero():
    cache = LRUCache(0)
    cache.put(1, 10)
    assert cache.get(1) == -1


def test_put_existing_key_updates_value_and_order():
    cache = LRUCache(2)
    cache.put(1, 10)
    cache.put(2, 20)
    cache.put(1, 100)
    cache.put(3, 30)
    assert cache.get(1) == 100
    assert cache.get(2) == -1


def test_repeated_get():
    cache = LRUCache(2)
    cache.put(1, 10)
    assert cache.get(1) == 10
    assert cache.get(1) == 10


def test_many_operations():
    cache = LRUCache(128)
    for i in range(10_000):
        cache.put(i, i * 2)
        assert cache.get(i) == i * 2
    assert cache.get(0) == -1
    assert cache.get(9_999) == 19_998


def test_get_nonexistent_returns_negative_one():
    cache = LRUCache(3)
    assert cache.get(999) == -1


def test_put_same_key_multiple_times():
    cache = LRUCache(1)
    cache.put(1, 10)
    cache.put(1, 20)
    cache.put(1, 30)
    assert cache.get(1) == 30


def test_negative_keys_and_values():
    cache = LRUCache(2)
    cache.put(-1, -100)
    cache.put(-2, -200)
    assert cache.get(-1) == -100
    assert cache.get(-2) == -200


def test_string_keys():
    cache = LRUCache(2)
    cache.put("a", 1)
    cache.put("b", 2)
    cache.put("c", 3)
    assert cache.get("a") == -1
    assert cache.get("c") == 3


def test_large_capacity():
    cache = LRUCache(10_000)
    for i in range(10_000):
        cache.put(i, i)
    assert cache.get(0) == 0
    assert cache.get(9_999) == 9_999
