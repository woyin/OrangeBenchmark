"""Custom scoring for sorting-algo problem."""

def score_performance(generated_code: str, work_dir: str) -> float:
    """Score performance based on code efficiency indicators."""
    code = generated_code.lower()
    # Check for O(n log n) algorithm indicators
    has_merge = "merge" in code
    has_divide = code.count("[:") >= 1 or "mid" in code
    has_quicksort = "quick" in code and "pivot" in code

    if has_merge and has_divide:
        return 1.0
    elif has_quicksort:
        return 0.95
    elif "sort(" in code:
        # Using built-in sort — correct but not implementing from scratch
        return 0.4
    else:
        return 0.5
