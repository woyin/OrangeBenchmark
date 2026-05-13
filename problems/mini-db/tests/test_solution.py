import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "mini_db_solution",
    Path(__file__).resolve().parents[1] / "solution.py",
)
solution = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(solution)
MiniDB = solution.MiniDB


def test_basic_get_set_delete():
    db = MiniDB()
    db.set("a", "1")
    assert db.get("a") == "1"
    assert db.delete("a") is True
    assert db.get("a") is None
    assert db.delete("a") is False


def test_scan_and_count():
    db = MiniDB()
    db.set("user:1", "alice")
    db.set("user:2", "bob")
    db.set("item:1", "widget")
    assert db.scan("user:") == [("user:1", "alice"), ("user:2", "bob")]
    assert db.count("user:") == 2
    assert db.count("item:") == 1
    assert db.count("order:") == 0


def test_simple_transaction_commit():
    db = MiniDB()
    db.set("x", "1")
    db.begin()
    db.set("x", "2")
    assert db.get("x") == "2"
    db.commit()
    assert db.get("x") == "2"


def test_simple_transaction_rollback():
    db = MiniDB()
    db.set("x", "1")
    db.begin()
    db.set("x", "2")
    db.rollback()
    assert db.get("x") == "1"


def test_nested_transaction():
    db = MiniDB()
    db.set("a", "0")
    db.begin()
    db.set("a", "1")
    db.begin()
    db.set("a", "2")
    assert db.get("a") == "2"
    db.commit()
    assert db.get("a") == "2"
    db.rollback()
    assert db.get("a") == "0"


def test_nested_commit_all():
    db = MiniDB()
    db.set("a", "0")
    db.begin()
    db.set("a", "1")
    db.begin()
    db.set("a", "2")
    db.commit()
    db.commit()
    assert db.get("a") == "2"


def test_delete_in_transaction():
    db = MiniDB()
    db.set("k", "v")
    db.begin()
    db.delete("k")
    assert db.get("k") is None
    db.rollback()
    assert db.get("k") == "v"


def test_commit_without_transaction_raises():
    db = MiniDB()
    try:
        db.commit()
        raise AssertionError("expected RuntimeError")
    except RuntimeError:
        pass


def test_rollback_without_transaction_raises():
    db = MiniDB()
    try:
        db.rollback()
        raise AssertionError("expected RuntimeError")
    except RuntimeError:
        pass


def test_scan_in_transaction():
    db = MiniDB()
    db.set("k1", "a")
    db.begin()
    db.set("k2", "b")
    db.delete("k1")
    result = db.scan("k")
    assert ("k2", "b") in result
    assert all(k != "k1" for k, _ in result)
    db.commit()
    assert db.count("k") == 1


def test_large_dataset():
    db = MiniDB()
    for i in range(1000):
        db.set(f"key:{i}", f"val:{i}")
    assert db.count("key:") == 1000
    assert db.get("key:500") == "val:500"


def test_overwrite_value():
    db = MiniDB()
    db.set("x", "a")
    db.set("x", "b")
    assert db.get("x") == "b"


def test_empty_scan():
    db = MiniDB()
    assert db.scan("any") == []
    assert db.count("any") == 0
