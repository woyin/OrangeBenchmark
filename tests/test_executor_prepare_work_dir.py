from pathlib import Path

from runner.executor import prepare_work_dir


def test_prepare_work_dir_copies_python_tests_and_conftest(tmp_path: Path):
    problem_dir = tmp_path / "problem"
    (problem_dir / "tests").mkdir(parents=True)
    (problem_dir / "tests" / "test_solution.py").write_text("def test_ok(): assert True\n")
    (problem_dir / "conftest.py").write_text("# conftest\n")

    work_dir = prepare_work_dir(problem_dir, tmp_path / "work")

    assert (work_dir / "tests" / "test_solution.py").exists()
    assert (work_dir / "conftest.py").exists()


def test_prepare_work_dir_copies_declared_copy_paths(tmp_path: Path):
    problem_dir = tmp_path / "rust-problem"
    (problem_dir / "src").mkdir(parents=True)
    (problem_dir / "tests").mkdir()
    (problem_dir / "src" / "lib.rs").write_text(
        "pub fn add(a: f64, b: f64) -> f64 { a + b }\n"
    )
    (problem_dir / "Cargo.toml").write_text(
        '[package]\nname = "calc"\nversion = "0.1.0"\nedition = "2021"\n'
    )
    problem_config = {
        "copy_paths": ["Cargo.toml", "src", "tests"],
    }

    work_dir = prepare_work_dir(problem_dir, tmp_path / "work", problem_config)

    assert (work_dir / "Cargo.toml").exists()
    assert (work_dir / "src" / "lib.rs").exists()
    assert (work_dir / "tests").exists()
