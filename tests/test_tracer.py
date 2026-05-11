"""Tests for runner/tracer.py."""

import time
from pathlib import Path

from runner.tracer import RawTracer, CliAgentTracer, TraceResult


def test_raw_tracer_records_api_call():
    tracer = RawTracer(model="gpt-4o")
    tracer.start_session()

    tracer.record_api_call(input_tokens=100, output_tokens=50, duration_ms=500, model_name="gpt-4o")

    result = tracer.finish_session()
    assert result.mode == "raw"
    assert result.summary.total_api_calls == 1
    assert result.summary.total_input_tokens == 100
    assert result.summary.total_output_tokens == 50
    assert result.summary.conversation_turns == 1
    assert len(result.events) == 1
    assert result.events[0].type == "api_call"


def test_raw_tracer_accumulates_multiple_calls():
    tracer = RawTracer(model="gpt-4o")
    tracer.start_session()

    tracer.record_api_call(input_tokens=100, output_tokens=50)
    tracer.record_api_call(input_tokens=200, output_tokens=80)

    result = tracer.finish_session()
    assert result.summary.total_api_calls == 2
    assert result.summary.total_input_tokens == 300
    assert result.summary.total_output_tokens == 130


def test_raw_tracer_records_duration():
    tracer = RawTracer(model="gpt-4o")
    tracer.start_session()
    time.sleep(0.05)

    result = tracer.finish_session()
    assert result.summary.total_duration_ms >= 50


def test_cli_agent_tracer_records_file_operations():
    tracer = CliAgentTracer(model="claude-sonnet-4", agent="claude-code", problem="two-sum")
    tracer.start_session()

    tracer.record_file_read("solution.py", size=100)
    tracer.record_file_write("solution.py", size=200)
    tracer.record_command_exec("pytest tests/ -v", exit_code=0)

    result = tracer.finish_session()
    assert result.mode == "agent"
    assert result.summary.file_reads == 1
    assert result.summary.file_writes == 1
    assert result.summary.command_executions == 1
    assert result.summary.total_tool_calls == 3


def test_cli_agent_tracer_records_conversation_turns():
    tracer = CliAgentTracer(model="claude-sonnet-4", agent="claude-code", problem="two-sum")
    tracer.start_session()

    tracer.record_conversation_turn(1)
    tracer.record_conversation_turn(2)
    tracer.record_conversation_turn(3)

    result = tracer.finish_session()
    assert result.summary.conversation_turns == 3


def test_trace_result_to_dict():
    tracer = RawTracer(model="gpt-4o")
    tracer.start_session()
    tracer.record_api_call(input_tokens=100, output_tokens=50, duration_ms=500, model_name="gpt-4o")

    result = tracer.finish_session()
    d = result.to_dict()

    assert d["model"] == "gpt-4o"
    assert d["mode"] == "raw"
    assert len(d["events"]) == 1
    assert d["events"][0]["type"] == "api_call"
    assert d["summary"]["total_api_calls"] == 1


def test_trace_result_save_to_file(tmp_path: Path):
    tracer = RawTracer(model="gpt-4o")
    tracer.start_session()
    tracer.record_api_call(input_tokens=100, output_tokens=50)

    result = tracer.finish_session()
    path = tmp_path / "trace.json"
    result.save_to_file(path)

    assert path.exists()
    import json
    with open(path) as f:
        data = json.load(f)
    assert data["model"] == "gpt-4o"
    assert len(data["events"]) == 1
