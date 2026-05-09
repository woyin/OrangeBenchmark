from collections import defaultdict, deque
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from typing import Any, Callable


class TaskScheduler:
    def __init__(self, max_workers: int = 4):
        self.max_workers = max(1, max_workers)
        self.tasks: dict[str, Callable[[], Any]] = {}
        self.dependencies: dict[str, set[str]] = {}

    def add_task(self, name: str, fn: Callable, dependencies: list[str] | None = None) -> None:
        self.tasks[name] = fn
        self.dependencies[name] = set(dependencies or [])

    def run_all(self) -> dict[str, Any]:
        if not self.tasks:
            return {}
        self._detect_cycle()

        remaining_deps = {name: set(self.dependencies.get(name, set())) for name in self.tasks}
        dependents: dict[str, set[str]] = defaultdict(set)
        for name, deps in remaining_deps.items():
            for dep in deps:
                dependents[dep].add(name)

        ready = deque(name for name, deps in remaining_deps.items() if not deps)
        running = {}
        completed = set()
        results: dict[str, Any] = {}

        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            while ready or running:
                while ready and len(running) < self.max_workers:
                    name = ready.popleft()
                    running[pool.submit(self.tasks[name])] = name

                done, _ = wait(running, return_when=FIRST_COMPLETED)
                for future in done:
                    name = running.pop(future)
                    try:
                        results[name] = future.result()
                    except Exception as exc:
                        results[name] = {"error": str(exc)}
                    completed.add(name)
                    for dependent in dependents[name]:
                        remaining_deps[dependent].discard(name)
                        if not remaining_deps[dependent] and dependent not in completed:
                            if dependent not in running.values() and dependent not in ready:
                                ready.append(dependent)

        return results

    def _detect_cycle(self) -> None:
        deps = {name: set(self.dependencies.get(name, set())) for name in self.tasks}
        ready = deque(name for name, task_deps in deps.items() if not task_deps)
        visited = 0
        dependents: dict[str, set[str]] = defaultdict(set)
        for name, task_deps in deps.items():
            for dep in task_deps:
                if dep not in self.tasks:
                    raise KeyError(f"Unknown dependency: {dep}")
                dependents[dep].add(name)

        while ready:
            name = ready.popleft()
            visited += 1
            for dependent in dependents[name]:
                deps[dependent].discard(name)
                if not deps[dependent]:
                    ready.append(dependent)

        if visited != len(self.tasks):
            raise ValueError("Cycle detected")
