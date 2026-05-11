# OrangeBenchmark — Agent 行为追踪与元数据评分设计

> 日期：2026-05-11
> 目标：为 OrangeBenchmark 增加 Agent 行为追踪与元数据收集能力，支持 raw 和 agent 两种模式，并新增行为评分维度。

---

## 1. 目标与范围

### 1.1 目标
- **统一追踪层**：为 raw 单轮 API 调用和 agent CLI 多轮调用建立统一的追踪与元数据收集机制。
- **行为评分**：新增 `cost_efficiency`、`tool_efficiency` 等评分维度，让评测不仅看结果，也看过程代价。
- **数据存储**：同时存入 results JSON（便于排名展示）和独立 trace 文件（便于深度分析）。

### 1.2 非目标
- 不修改现有的 correctness / code_quality / performance 评分逻辑。
- 不修改 reporter 的终端表格展示格式（但会新增列数据）。
- 不实现 MCP 协议 Agent 集成（留作未来扩展）。

---

## 2. 架构设计

### 2.1 统一追踪层（`runner/tracer.py`）

引入 `AgentTracer` 抽象基类，raw 和 agent 模式共享同一套追踪接口：

```
AgentTracer (ABC)
├── RawTracer        — 包装 OpenAI API 调用，记录 token/耗时
└── CliAgentTracer   — 包装 CLI Agent 调用，记录工具/文件/命令
```

**核心方法**：
- `start_session()` — 开始追踪会话
- `record_event(type, **kwargs)` — 记录单个事件
- `finish_session() -> TraceResult` — 结束并返回追踪摘要

### 2.2 Raw 模式追踪

在 `executor.py` 的 `_run_raw()` 中，通过 `RawTracer` 包装 OpenAI 客户端调用：

**记录字段**：
- `input_tokens` — 请求 token 数
- `output_tokens` — 响应 token 数
- `api_calls` — API 调用次数（raw 模式固定为 1）
- `duration_ms` — 调用耗时
- `model_name` — 实际使用的模型名称

### 2.3 Agent 模式追踪

新增 `runner/agent_wrapper.py`，实现 `CliAgentWrapper` 抽象基类：

```
CliAgentWrapper (ABC)
├── ClaudeCodeWrapper  — 调用 `claude code` CLI
└── CodexWrapper       — 调用 `codex` CLI
```

**调用方式**：直接 subprocess 启动 CLI，传入 `work_dir` 和 `prompt` 作为参数。

**拦截与追踪**：
- 方式 A（本阶段）：通过解析 CLI 的输出日志（stdout/stderr）提取工具调用信息。Claude Code 和 Codex CLI 在执行工具调用时通常会在终端输出操作记录。
- 方式 B（未来）：若 CLI 支持输出结构化日志（如 `--json-log`），则直接解析。

**记录事件类型**：
- `tool_call` — 工具调用（读文件、写文件、执行命令等）
- `file_read` — 读取文件
- `file_write` — 写入文件
- `command_exec` — 执行 shell 命令
- `conversation_turn` — 对话轮次标记

### 2.4 数据流

```
runner/main.py (run command)
    ↓ 对每个 combo × problem
executor.py::run_task()
    ↓ 根据 agent_type 选择模式
    ├─ raw: RawTracer + _run_raw()
    └─ agent: CliAgentTracer + CliAgentWrapper
    ↓ 返回 (generated_code, trace_result)
scorer.py::score_problem()
    ↓ 计算原有维度 + 新增行为维度
    ↓ 合并 trace 到 problem_result
main.py 存储
    ├─ results/YYYY-MM-DDTHHMMSS.json
    └─ traces/YYYY-MM-DDTHHMMSS/<combo>/<problem>.json
```

---

## 3. 数据模型

### 3.1 Trace 事件结构

```json
{
  "timestamp": "2026-05-11T10:00:00",
  "model": "gpt-4o",
  "agent": "raw-api",
  "problem": "two-sum",
  "mode": "raw",
  "events": [
    {
      "type": "api_call",
      "input_tokens": 150,
      "output_tokens": 80,
      "duration_ms": 1200,
      "timestamp": "2026-05-11T10:00:01"
    }
  ],
  "summary": {
    "total_api_calls": 1,
    "total_input_tokens": 150,
    "total_output_tokens": 80,
    "total_duration_ms": 1200
  }
}
```

### 3.2 Agent 模式 Trace 示例

```json
{
  "timestamp": "2026-05-11T10:00:00",
  "model": "claude-sonnet-4",
  "agent": "claude-code",
  "problem": "two-sum",
  "mode": "agent",
  "events": [
    {"type": "conversation_turn", "turn": 1, "timestamp": "..."},
    {"type": "file_read", "path": "problem.yaml", "timestamp": "..."},
    {"type": "file_write", "path": "solution.py", "size": 256, "timestamp": "..."},
    {"type": "command_exec", "command": "pytest", "exit_code": 0, "timestamp": "..."},
    {"type": "conversation_turn", "turn": 2, "timestamp": "..."}
  ],
  "summary": {
    "total_tool_calls": 5,
    "file_reads": 2,
    "file_writes": 1,
    "command_executions": 2,
    "conversation_turns": 3
  }
}
```

### 3.3 Results JSON 中的 trace 字段

每个 `problem_result` 新增可选 `trace` 字段：

```json
{
  "name": "two-sum",
  "scores": {"correctness": 1.0, "code_quality": 0.95, "cost_efficiency": 0.85},
  "total": 0.94,
  "status": "pass",
  "duration_seconds": 3.2,
  "trace": {
    "total_api_calls": 1,
    "total_input_tokens": 150,
    "total_output_tokens": 80,
    "total_tool_calls": 0,
    "conversation_turns": 1
  }
}
```

---

## 4. 新增评分维度

### 4.1 `cost_efficiency`（成本效率）

**定义**：用尽可能少的 token 解决问题。

**计算逻辑**：
```
cost_efficiency = correctness_score * max(0.0, 1.0 - (total_tokens / TOKEN_BUDGET))
```

- `total_tokens = input_tokens + output_tokens`
- `TOKEN_BUDGET`：按难度预设的 token 预算
  - easy: 2000 tokens
  - medium: 5000 tokens
  - hard: 10000 tokens
  - 可在 `problem.yaml` 的 `scoring` 配置中覆盖
- 乘以 `correctness_score` 确保：没做对题，cost_efficiency 也为低分

### 4.2 `tool_efficiency`（工具效率）

**定义**：用尽可能少的工具调用解决问题。

**计算逻辑**：
```
tool_efficiency = correctness_score * max(0.0, 1.0 - (tool_calls / TOOL_BUDGET))
```

- `tool_calls`：总工具调用次数（文件读写 + 命令执行）
- `TOOL_BUDGET`：按难度预设的工具调用预算
  - easy: 5 次
  - medium: 10 次
  - hard: 20 次
  - 可在 `problem.yaml` 中覆盖
- raw 模式固定 tool_calls = 0，tool_efficiency = correctness_score（即不扣分）

### 4.3 维度配置

新增维度通过 `problem.yaml` 的 `scoring.dimensions` 配置，与现有维度并列：

```yaml
scoring:
  dimensions:
    - name: correctness
      weight: 0.4
    - name: code_quality
      weight: 0.2
    - name: performance
      weight: 0.2
    - name: cost_efficiency
      weight: 0.1
    - name: tool_efficiency
      weight: 0.1
  behavior:
    token_budget:
      easy: 2000
      medium: 5000
      hard: 10000
    tool_budget:
      easy: 5
      medium: 10
      hard: 20
```

### 4.4 向后兼容

- 旧题目无 `behavior` 配置时，使用上述默认值。
- `scorer.py` 的 `_default_score` 中新增 `cost_efficiency` 和 `tool_efficiency` 分支。
- 若 trace 数据不可用（如旧评测结果），返回 `correctness_score * 0.5` 作为保守估计。

---

## 5. CLI 变化

### 5.1 `orangebench run`

新增选项：
- `--trace-dir <path>` — 指定 trace 文件存储目录（默认：`traces/`）
- `--no-trace` — 禁用独立 trace 文件输出（仍保留 results JSON 中的 trace 摘要）

### 5.2 `orangebench show`

新增选项：
- `--trace` — 显示详细 trace 事件列表

---

## 6. 文件变更清单

### 新增文件
- `runner/tracer.py` — 统一追踪层（AgentTracer、RawTracer、CliAgentTracer）
- `runner/agent_wrapper.py` — CLI Agent wrapper（CliAgentWrapper、ClaudeCodeWrapper、CodexWrapper）
- `runner/scoring/behavior.py` — 行为评分维度计算（cost_efficiency、tool_efficiency）

### 修改文件
- `runner/executor.py` — 集成 tracer，修改 `run_task` 返回值包含 trace 数据
- `runner/main.py` — 修改 `run` 命令，存储 trace 到 results JSON 和独立文件
- `runner/scorer.py` — 新增 `cost_efficiency` 和 `tool_efficiency` 默认评分逻辑
- `pyproject.toml` — 新增 `runner/scoring` package 声明

### 不变文件
- `runner/reporter.py` — 格式不变，但会自动展示新增维度列
- 所有现有题目配置（可选升级以使用新维度）

---

## 7. 风险与缓解

| 风险 | 缓解措施 |
|------|---------|
| CLI Agent 输出格式不稳定，难以解析 | 先实现 stdout 解析，失败时回退到仅记录调用次数和耗时 |
| token 消耗数据不是所有 provider 都提供 | OpenAI 兼容 API 的 `usage` 字段已标准化；不支持时 trace 中标记为 null |
| 新增维度导致旧结果不可比 | 新增维度默认 weight=0，用户显式配置后才计入总分 |
| Agent 模式超时难以优雅终止 | 使用 `timeout` 库或 subprocess timeout，trace 中记录 `status: timeout` |

---

## 8. 验收标准

- [ ] `orangebench run` 执行后，`results/*.json` 中每个 problem_result 包含 `trace` 字段
- [ ] `traces/` 目录下生成独立 trace JSON 文件，结构与 3.1 一致
- [ ] raw 模式能正确记录 input_tokens、output_tokens、api_calls、duration
- [ ] agent 模式能正确记录 tool_calls、file_reads、file_writes、command_executions
- [ ] 配置 behavior 维度的题目，results 中包含 cost_efficiency 和 tool_efficiency 评分
- [ ] 所有现有测试通过，向后兼容
