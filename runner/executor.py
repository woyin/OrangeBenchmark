"""Prepare work directories for scoring."""

import shutil
from pathlib import Path


def prepare_work_dir(
    problem_dir: Path,
    base_work_dir: Path,
    problem_config: dict | None = None,
) -> Path:
    """Create a temp work dir and copy problem scaffold files into it."""
    work_dir = base_work_dir / problem_dir.name
    work_dir.mkdir(parents=True, exist_ok=True)

    copy_paths = (problem_config or {}).get("copy_paths")
    if copy_paths:
        for rel_path in copy_paths:
            src = problem_dir / rel_path
            dst = work_dir / rel_path
            if not src.exists():
                continue
            if src.is_dir():
                if dst.exists():
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
            else:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
        return work_dir

    tests_src = problem_dir / "tests"
    if tests_src.exists():
        tests_dst = work_dir / "tests"
        if tests_dst.exists():
            shutil.rmtree(tests_dst)
        shutil.copytree(tests_src, tests_dst)

    conftest_src = problem_dir / "conftest.py"
    if conftest_src.exists():
        shutil.copy2(conftest_src, work_dir / "conftest.py")

    return work_dir
