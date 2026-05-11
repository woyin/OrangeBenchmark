"""Tests for runner/agent_wrapper.py."""

from pathlib import Path

from runner.agent_wrapper import (
    ClaudeCodeWrapper,
    CodexWrapper,
    get_agent_wrapper,
    AGENT_WRAPPERS,
)


def test_agent_wrappers_registry():
    assert "claude-code" in AGENT_WRAPPERS
    assert "codex" in AGENT_WRAPPERS
    assert AGENT_WRAPPERS["claude-code"] is ClaudeCodeWrapper
    assert AGENT_WRAPPERS["codex"] is CodexWrapper


def test_get_agent_wrapper_returns_none_for_raw():
    agent_cfg = {"name": "raw-api", "type": "raw"}
    model_cfg = {"model": "gpt-4o"}
    wrapper = get_agent_wrapper(agent_cfg, model_cfg)
    assert wrapper is None


def test_get_agent_wrapper_for_claude_code():
    agent_cfg = {"name": "claude-code", "type": "agent"}
    model_cfg = {"model": "claude-sonnet-4"}
    wrapper = get_agent_wrapper(agent_cfg, model_cfg)
    assert isinstance(wrapper, ClaudeCodeWrapper)
    assert wrapper.model == "claude-sonnet-4"
    assert wrapper.agent_name == "claude-code"


def test_get_agent_wrapper_for_codex():
    agent_cfg = {"name": "codex", "type": "agent"}
    model_cfg = {"model": "o4-mini"}
    wrapper = get_agent_wrapper(agent_cfg, model_cfg)
    assert isinstance(wrapper, CodexWrapper)
    assert wrapper.model == "o4-mini"


def test_get_agent_wrapper_for_unknown_returns_none():
    agent_cfg = {"name": "unknown-agent", "type": "agent"}
    model_cfg = {"model": "gpt-4o"}
    wrapper = get_agent_wrapper(agent_cfg, model_cfg)
    assert wrapper is None


def test_claude_code_wrapper_extract_path():
    wrapper = ClaudeCodeWrapper()
    assert wrapper._extract_path("Read: `/tmp/solution.py`") == "/tmp/solution.py"
    assert wrapper._extract_path("Writing to solution.py done") == "solution.py"
    assert wrapper._extract_path("no path here") is None


def test_codex_wrapper_extract_path():
    wrapper = CodexWrapper()
    assert wrapper._extract_path("file_read: `/home/user/app.js`") == "/home/user/app.js"
    assert wrapper._extract_path("no path here") is None
