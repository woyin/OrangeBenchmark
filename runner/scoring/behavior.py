"""Behavioral scoring dimensions: cost_efficiency and tool_efficiency."""

from typing import Any


_DEFAULT_TOKEN_BUDGETS = {"easy": 2000, "medium": 5000, "hard": 10000}
_DEFAULT_TOOL_BUDGETS = {"easy": 5, "medium": 10, "hard": 20}


def _get_budget(behavior_config: dict, key: str, difficulty: str, defaults: dict) -> int:
    """Get budget from config or fall back to defaults by difficulty."""
    config_budgets = behavior_config.get(key, {})
    if difficulty in config_budgets:
        return int(config_budgets[difficulty])
    return defaults.get(difficulty, 2000)


def score_cost_efficiency(
    generated_code: str,
    work_dir: str,
    trace_data: dict[str, Any] | None = None,
    problem_config: dict | None = None,
) -> float:
    """
    Cost efficiency: reward solving problems with fewer tokens.

    cost_efficiency = correctness_score * max(0.0, 1.0 - (total_tokens / TOKEN_BUDGET))

    If trace_data is not available, returns correctness * 0.5 as a conservative estimate.
    """
    if trace_data is None:
        return 0.5  # Conservative estimate when no trace data

    problem_config = problem_config or {}
    difficulty = problem_config.get("difficulty", "medium")
    behavior = problem_config.get("scoring", {}).get("behavior", {})
    token_budget = _get_budget(behavior, "token_budget", difficulty, _DEFAULT_TOKEN_BUDGETS)

    input_tokens = trace_data.get("total_input_tokens", 0)
    output_tokens = trace_data.get("total_output_tokens", 0)
    total_tokens = input_tokens + output_tokens

    if total_tokens == 0:
        return 0.0

    efficiency = max(0.0, 1.0 - (total_tokens / token_budget))
    return round(efficiency, 4)


def score_tool_efficiency(
    generated_code: str,
    work_dir: str,
    trace_data: dict[str, Any] | None = None,
    problem_config: dict | None = None,
) -> float:
    """
    Tool efficiency: reward solving problems with fewer tool calls.

    tool_efficiency = correctness_score * max(0.0, 1.0 - (tool_calls / TOOL_BUDGET))

    If trace_data is not available, returns 0.5 as a conservative estimate.
    """
    if trace_data is None:
        return 0.5  # Conservative estimate when no trace data

    problem_config = problem_config or {}
    difficulty = problem_config.get("difficulty", "medium")
    behavior = problem_config.get("scoring", {}).get("behavior", {})
    tool_budget = _get_budget(behavior, "tool_budget", difficulty, _DEFAULT_TOOL_BUDGETS)

    tool_calls = trace_data.get("total_tool_calls", 0)
    if tool_calls == 0:
        # Raw mode has no tool calls - score should reflect that
        return 0.0

    efficiency = max(0.0, 1.0 - (tool_calls / tool_budget))
    return round(efficiency, 4)
