"""Custom scoring (optional). Delete this file to use default scoring."""

def score_correctness(generated_code: str, work_dir: str) -> float:
    """Run tests and return 0.0~1.0 pass rate. Delete to use default."""
    # Default: pytest pass rate is used automatically when this function is absent
    raise NotImplementedError

def score_performance(generated_code: str, work_dir: str) -> float:
    """Runtime efficiency: time + memory. Return 0.0~1.0."""
    raise NotImplementedError
