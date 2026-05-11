"""Unified tracing layer for raw API calls and CLI agent executions."""

import json
import time
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class TraceEvent:
    type: str
    timestamp: str = ""
    data: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


@dataclass
class TraceSummary:
    total_api_calls: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_duration_ms: int = 0
    total_tool_calls: int = 0
    file_reads: int = 0
    file_writes: int = 0
    command_executions: int = 0
    conversation_turns: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v > 0}


@dataclass
class TraceResult:
    model: str
    agent: str
    problem: str
    mode: str = "raw"
    events: list[TraceEvent] = field(default_factory=list)
    summary: TraceSummary = field(default_factory=TraceSummary)
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "model": self.model,
            "agent": self.agent,
            "problem": self.problem,
            "mode": self.mode,
            "events": [{"type": e.type, "timestamp": e.timestamp, **e.data} for e in self.events],
            "summary": self.summary.to_dict(),
        }

    def save_to_file(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)


class AgentTracer(ABC):
    """Abstract base class for tracking agent behavior."""

    def __init__(self, model: str, agent: str, problem: str, mode: str = "raw"):
        self.result = TraceResult(model=model, agent=agent, problem=problem, mode=mode)
        self._session_start: float = 0.0

    def start_session(self) -> None:
        self._session_start = time.time()
        self.result.events = []

    def record_event(self, event_type: str, **kwargs: Any) -> None:
        event = TraceEvent(type=event_type, data=kwargs)
        self.result.events.append(event)
        self._update_summary(event)

    def finish_session(self) -> TraceResult:
        self.result.summary.total_duration_ms = int(
            (time.time() - self._session_start) * 1000
        )
        return self.result

    @abstractmethod
    def _update_summary(self, event: TraceEvent) -> None:
        pass


class RawTracer(AgentTracer):
    """Tracer for single-turn raw API calls."""

    def __init__(self, model: str):
        super().__init__(model=model, agent="raw-api", problem="", mode="raw")

    def _update_summary(self, event: TraceEvent) -> None:
        if event.type == "api_call":
            self.result.summary.total_api_calls += 1
            self.result.summary.total_input_tokens += event.data.get(
                "input_tokens", 0
            )
            self.result.summary.total_output_tokens += event.data.get(
                "output_tokens", 0
            )
            self.result.summary.conversation_turns = 1

    def record_api_call(
        self,
        input_tokens: int = 0,
        output_tokens: int = 0,
        duration_ms: int = 0,
        model_name: str = "",
    ) -> None:
        self.record_event(
            "api_call",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            duration_ms=duration_ms,
            model_name=model_name,
        )


class CliAgentTracer(AgentTracer):
    """Tracer for multi-turn CLI agent executions."""

    def __init__(self, model: str, agent: str, problem: str):
        super().__init__(model=model, agent=agent, problem=problem, mode="agent")
        # conversation_turns starts at 0 for agent mode (we track each turn explicitly)
        self.result.summary.conversation_turns = 0

    def _update_summary(self, event: TraceEvent) -> None:
        if event.type in ("file_read", "file_write", "command_exec"):
            self.result.summary.total_tool_calls += 1
        if event.type == "file_read":
            self.result.summary.file_reads += 1
        elif event.type == "file_write":
            self.result.summary.file_writes += 1
        elif event.type == "command_exec":
            self.result.summary.command_executions += 1
        elif event.type == "conversation_turn":
            self.result.summary.conversation_turns += 1

    def record_file_read(self, path: str, size: int = 0) -> None:
        self.record_event("file_read", path=path, size=size)

    def record_file_write(self, path: str, size: int = 0) -> None:
        self.record_event("file_write", path=path, size=size)

    def record_command_exec(self, command: str, exit_code: int = 0) -> None:
        self.record_event("command_exec", command=command, exit_code=exit_code)

    def record_conversation_turn(self, turn: int) -> None:
        self.record_event("conversation_turn", turn=turn)
