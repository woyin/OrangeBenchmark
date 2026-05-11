"""CLI Agent wrappers for launching external coding agents."""

import re
import subprocess
import time
from abc import ABC, abstractmethod
from pathlib import Path

from runner.tracer import CliAgentTracer, TraceResult


class CliAgentWrapper(ABC):
    """Abstract base class for CLI agent wrappers."""

    def __init__(self, model: str, agent_name: str, timeout: int = 120):
        self.model = model
        self.agent_name = agent_name
        self.timeout = timeout

    def run(self, prompt: str, work_dir: Path, problem_name: str) -> tuple[str, TraceResult]:
        """Run the agent and return (output, trace)."""
        tracer = CliAgentTracer(
            model=self.model, agent=self.agent_name, problem=problem_name
        )
        tracer.start_session()
        tracer.record_conversation_turn(1)

        try:
            output = self._execute(prompt, work_dir, tracer, self.timeout)
            tracer.record_conversation_turn(2)
            return output, tracer.finish_session()
        except subprocess.TimeoutExpired:
            tracer.record_conversation_turn(2)
            result = tracer.finish_session()
            return "", result

    @abstractmethod
    def _execute(
        self, prompt: str, work_dir: Path, tracer: CliAgentTracer, timeout: int
    ) -> str:
        """Execute the CLI agent and return generated code."""
        pass


class ClaudeCodeWrapper(CliAgentWrapper):
    """Wrapper for Claude Code CLI (`claude`)."""

    def __init__(self, model: str = "claude-sonnet-4", timeout: int = 120):
        super().__init__(model=model, agent_name="claude-code", timeout=timeout)

    def _execute(
        self, prompt: str, work_dir: Path, tracer: CliAgentTracer, timeout: int
    ) -> str:
        result = subprocess.run(
            [
                "claude",
                "--model", self.model,
                "--output-format", "json",
                "--print", prompt,
            ],
            cwd=str(work_dir),
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        # Parse stdout for trace data (tool calls, file operations)
        self._parse_output(result.stdout, tracer)

        # Extract generated code from JSON output or stdout
        return self._extract_code(result.stdout, work_dir)

    def _parse_output(self, stdout: str, tracer: CliAgentTracer) -> None:
        """Parse agent output to extract trace events."""
        for line in stdout.split("\n"):
            line = line.strip()
            if "Read:" in line or "Reading" in line:
                path = self._extract_path(line)
                if path:
                    tracer.record_file_read(path)
            elif "Write:" in line or "Wrote" in line:
                path = self._extract_path(line)
                if path:
                    tracer.record_file_write(path)
            elif "Run:" in line or "Executing" in line:
                cmd = line.split(":", 1)[-1].strip() if ":" in line else line
                tracer.record_command_exec(cmd)

    def _extract_path(self, line: str) -> str | None:
        """Extract a file path from a log line."""
        match = re.search(r"`?(/?[^\s`]+\.[a-zA-Z]+)`?", line)
        return match.group(1) if match else None

    def _extract_code(self, stdout: str, work_dir: Path) -> str:
        """Extract code from agent output."""
        import json as _json
        try:
            data = _json.loads(stdout)
            content = data.get("content", data.get("result", ""))
            if content:
                return content
        except _json.JSONDecodeError:
            pass

        # Fall back to checking solution files in work_dir
        for name in ("solution.py", "solution.java", "solution.cs"):
            path = work_dir / name
            if path.exists():
                return path.read_text()
        return ""


class CodexWrapper(CliAgentWrapper):
    """Wrapper for OpenAI Codex CLI (`codex`)."""

    def __init__(self, model: str = "o4-mini", timeout: int = 120):
        super().__init__(model=model, agent_name="codex", timeout=timeout)

    def _execute(
        self, prompt: str, work_dir: Path, tracer: CliAgentTracer, timeout: int
    ) -> str:
        result = subprocess.run(
            [
                "codex",
                "--model", self.model,
                "--approval-mode", "full-auto",
                prompt,
            ],
            cwd=str(work_dir),
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        # Parse stdout for trace data
        self._parse_output(result.stdout, tracer)

        return self._extract_code(result.stdout, work_dir)

    def _parse_output(self, stdout: str, tracer: CliAgentTracer) -> None:
        """Parse agent output to extract trace events."""
        for line in stdout.split("\n"):
            line = line.strip()
            if "file_read" in line.lower() or "reading" in line.lower():
                path = self._extract_path(line)
                if path:
                    tracer.record_file_read(path)
            elif "file_write" in line.lower() or "writing" in line.lower():
                path = self._extract_path(line)
                if path:
                    tracer.record_file_write(path)
            elif "command" in line.lower() or "exec" in line.lower():
                cmd = line.split(":", 1)[-1].strip() if ":" in line else line
                tracer.record_command_exec(cmd)

    def _extract_path(self, line: str) -> str | None:
        """Extract a file path from a log line."""
        match = re.search(r"`?(/?[^\s`]+\.[a-zA-Z]+)`?", line)
        return match.group(1) if match else None

    def _extract_code(self, stdout: str, work_dir: Path) -> str:
        """Extract code from agent output."""
        for name in ("solution.py", "solution.java", "solution.cs"):
            path = work_dir / name
            if path.exists():
                return path.read_text()
        return ""


# Registry of available wrappers
AGENT_WRAPPERS: dict[str, type[CliAgentWrapper]] = {
    "claude-code": ClaudeCodeWrapper,
    "codex": CodexWrapper,
}


def get_agent_wrapper(agent_cfg: dict, model_cfg: dict) -> CliAgentWrapper | None:
    """Get an agent wrapper instance for the given agent config."""
    agent_name = agent_cfg.get("name", "")
    agent_type = agent_cfg.get("type", "")

    if agent_type != "agent":
        return None

    wrapper_cls = AGENT_WRAPPERS.get(agent_name)
    if wrapper_cls is None:
        return None

    return wrapper_cls(
        model=model_cfg.get("model", ""),
        timeout=agent_cfg.get("timeout", 120),
    )
