"""Tests for runner/scoring/behavior.py."""

from runner.scoring.behavior import score_cost_efficiency, score_tool_efficiency


def test_cost_efficiency_no_trace_data():
    score = score_cost_efficiency("", "/tmp", trace_data=None)
    assert score == 0.5  # conservative estimate


def test_cost_efficiency_zero_tokens():
    score = score_cost_efficiency("", "/tmp", trace_data={"total_input_tokens": 0, "total_output_tokens": 0})
    assert score == 0.0


def test_cost_efficiency_within_budget():
    # easy problem, budget = 2000, used 500
    trace = {"total_input_tokens": 300, "total_output_tokens": 200}
    config = {"difficulty": "easy"}
    score = score_cost_efficiency("", "/tmp", trace_data=trace, problem_config=config)
    # 1.0 - 500/2000 = 0.75
    assert score == 0.75


def test_cost_efficiency_over_budget():
    # easy problem, budget = 2000, used 3000
    trace = {"total_input_tokens": 2000, "total_output_tokens": 1000}
    config = {"difficulty": "easy"}
    score = score_cost_efficiency("", "/tmp", trace_data=trace, problem_config=config)
    # 1.0 - 3000/2000 = -0.5, clamped to 0.0
    assert score == 0.0


def test_cost_efficiency_custom_budget():
    trace = {"total_input_tokens": 500, "output_tokens": 0, "total_output_tokens": 0}
    config = {
        "difficulty": "easy",
        "scoring": {"behavior": {"token_budget": {"easy": 1000}}}
    }
    score = score_cost_efficiency("", "/tmp", trace_data=trace, problem_config=config)
    # 1.0 - 500/1000 = 0.5
    assert score == 0.5


def test_cost_efficiency_medium_default():
    trace = {"total_input_tokens": 2000, "total_output_tokens": 500}
    config = {"difficulty": "medium"}
    score = score_cost_efficiency("", "/tmp", trace_data=trace, problem_config=config)
    # 1.0 - 2500/5000 = 0.5
    assert score == 0.5


def test_cost_efficiency_hard_default():
    trace = {"total_input_tokens": 5000, "total_output_tokens": 2000}
    config = {"difficulty": "hard"}
    score = score_cost_efficiency("", "/tmp", trace_data=trace, problem_config=config)
    # 1.0 - 7000/10000 = 0.3
    assert score == 0.3


def test_tool_efficiency_no_trace_data():
    score = score_tool_efficiency("", "/tmp", trace_data=None)
    assert score == 0.5


def test_tool_efficiency_zero_tool_calls():
    # raw mode: no tool calls at all
    score = score_tool_efficiency("", "/tmp", trace_data={"total_tool_calls": 0})
    assert score == 0.0


def test_tool_efficiency_within_budget():
    trace = {"total_tool_calls": 3}
    config = {"difficulty": "easy"}
    score = score_tool_efficiency("", "/tmp", trace_data=trace, problem_config=config)
    # 1.0 - 3/5 = 0.4
    assert score == 0.4


def test_tool_efficiency_over_budget():
    trace = {"total_tool_calls": 15}
    config = {"difficulty": "easy"}
    score = score_tool_efficiency("", "/tmp", trace_data=trace, problem_config=config)
    # 1.0 - 15/5 = -2.0, clamped to 0.0
    assert score == 0.0


def test_tool_efficiency_custom_budget():
    trace = {"total_tool_calls": 5}
    config = {
        "difficulty": "easy",
        "scoring": {"behavior": {"tool_budget": {"easy": 10}}}
    }
    score = score_tool_efficiency("", "/tmp", trace_data=trace, problem_config=config)
    # 1.0 - 5/10 = 0.5
    assert score == 0.5
