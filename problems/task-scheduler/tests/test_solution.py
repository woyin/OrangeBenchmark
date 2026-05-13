import importlib.util
import time
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "task_scheduler_solution",
    Path(__file__).resolve().parents[1] / "solution.py",
)
solution = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(solution)
TaskScheduler = solution.TaskScheduler


def test_single_task_and_none_result():
    scheduler = TaskScheduler()
    scheduler.add_task("a", lambda: None)
    assert scheduler.run_all() == {"a": None}


def test_linear_chain_order():
    order = []
    scheduler = TaskScheduler(max_workers=4)
    scheduler.add_task("a", lambda: order.append("a") or "A")
    scheduler.add_task("b", lambda: order.append("b") or "B", ["a"])
    scheduler.add_task("c", lambda: order.append("c") or "C", ["b"])
    assert scheduler.run_all() == {"a": "A", "b": "B", "c": "C"}
    assert order == ["a", "b", "c"]


def test_diamond_dependencies():
    scheduler = TaskScheduler(max_workers=2)
    scheduler.add_task("a", lambda: "A")
    scheduler.add_task("b", lambda: "B", ["a"])
    scheduler.add_task("c", lambda: "C", ["a"])
    scheduler.add_task("d", lambda: "D", ["b", "c"])
    assert scheduler.run_all()["d"] == "D"


def test_cycle_detection():
    scheduler = TaskScheduler()
    scheduler.add_task("a", lambda: "A", ["c"])
    scheduler.add_task("b", lambda: "B", ["a"])
    scheduler.add_task("c", lambda: "C", ["b"])
    try:
        scheduler.run_all()
    except ValueError as exc:
        assert str(exc) == "Cycle detected"
    else:
        raise AssertionError("expected cycle detection")


def test_task_exception_is_collected():
    scheduler = TaskScheduler()
    scheduler.add_task("bad", lambda: (_ for _ in ()).throw(RuntimeError("boom")))
    result = scheduler.run_all()
    assert "boom" in str(result["bad"])


def test_empty_scheduler():
    assert TaskScheduler().run_all() == {}


def test_parallel_execution_is_faster_than_serial():
    def sleeper():
        time.sleep(0.2)
        return "ok"

    serial = TaskScheduler(max_workers=1)
    parallel = TaskScheduler(max_workers=4)
    for idx in range(4):
        serial.add_task(str(idx), sleeper)
        parallel.add_task(str(idx), sleeper)

    start = time.perf_counter()
    serial.run_all()
    serial_elapsed = time.perf_counter() - start

    start = time.perf_counter()
    parallel.run_all()
    parallel_elapsed = time.perf_counter() - start

    assert parallel_elapsed < serial_elapsed * 0.75


def test_duplicate_task_id_overwrites():
    scheduler = TaskScheduler()
    scheduler.add_task("a", lambda: "first")
    scheduler.add_task("a", lambda: "second")
    assert scheduler.run_all()["a"] == "second"


def test_missing_dependency():
    scheduler = TaskScheduler()
    scheduler.add_task("a", lambda: "A", ["nonexistent"])
    try:
        scheduler.run_all()
    except (ValueError, KeyError):
        pass
    else:
        raise AssertionError("expected error for missing dependency")


def test_many_independent_tasks():
    scheduler = TaskScheduler(max_workers=8)
    for i in range(20):
        scheduler.add_task(f"t{i}", lambda x=i: x * 2)
    result = scheduler.run_all()
    assert len(result) == 20
    assert result["t10"] == 20


def test_self_dependency():
    scheduler = TaskScheduler()
    scheduler.add_task("a", lambda: "A", ["a"])
    try:
        scheduler.run_all()
    except ValueError:
        pass
    else:
        raise AssertionError("expected cycle detection for self-dependency")


def test_task_returning_complex_type():
    scheduler = TaskScheduler()
    scheduler.add_task("a", lambda: [1, 2, 3])
    scheduler.add_task("b", lambda: {"key": "val"}, ["a"])
    result = scheduler.run_all()
    assert result["a"] == [1, 2, 3]
    assert result["b"] == {"key": "val"}
